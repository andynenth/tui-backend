#!/usr/bin/env bash
set -euo pipefail

export AWS_PAGER=""

# ===== User inputs (edit before running) =====
US_EAST_1_INSTANCE_IDS=() # e.g., ("i-xxxxxxxxxxxxxxxxx" "i-yyyyyyyyyyyyyyyyy"); leave () to auto-discover
AP_NORTHEAST_1_INSTANCE_IDS=() # e.g., ("i-aaaaaaaaaaaaaaaaa"); leave () to auto-discover
S3_BACKUP_BUCKET="s3://my-backup-bucket" # set to "" to skip data-only guidance
BACKUP_TAG_CASE="CASE-175942564000829"
BACKUP_NAME_PREFIX="pre-delete-backup"
DRY_RUN=true # set to false to create backups
ARCHIVE_COPY_REGION="" # e.g., "us-west-2"; set to "" to skip cross-region copy
MANIFEST_PATH="./backup-manifest.json"
# ============================================

REQUIRED_CMDS=(aws jq date)

TODAY=""
manifest_content="{}"
tmp_manifest=""
created_count=0
existing_count=0

log() {
  printf '[%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*" >&2
}

warn() {
  log "WARN: $*"
}

error() {
  printf '[%s] ERROR: %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*" >&2
}

die() {
  error "$1"
  exit "${2:-1}"
}

cleanup() {
  if [[ -n "$tmp_manifest" && -f "$tmp_manifest" ]]; then
    rm -f "$tmp_manifest"
  fi
}
trap cleanup EXIT

iso_timestamp() {
  local ts
  ts=$(date -Iseconds 2>/dev/null || true)
  if [[ -n "$ts" ]]; then
    printf '%s\n' "$ts"
  else
    date -u +"%Y-%m-%dT%H:%M:%SZ"
  fi
}

validate_prereqs() {
  local missing=0
  local cmd
  for cmd in "${REQUIRED_CMDS[@]}"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      missing=1
      case "$cmd" in
        aws)
          error "'aws' CLI v2 is required. Install guide: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
          ;;
        jq)
          error "'jq' is required. Install with: brew install jq (macOS) or sudo yum install -y jq (Amazon Linux)."
          ;;
        date)
          error "'date' command is required."
          ;;
        *)
          error "Missing required command: $cmd"
          ;;
      esac
    fi
  done
  if ((missing)); then
    exit 1
  fi
}

is_valid_instance_id() {
  [[ "$1" =~ ^i-([0-9a-f]{8}|[0-9a-f]{17})$ ]]
}

to_json_array() {
  if (($# == 0)); then
    jq -n '[]'
  else
    printf '%s\n' "$" | jq -R -s 'split("\n") | map(select(length>0))'
  fi
}

tag_resources() {
  local region="$1"
  local created_on="$2"
  local instance_id="$3"
  shift 3
  local -a resources=()
  while (($#)); do
    [[ -n "$1" ]] && resources+=("$1")
    shift || true
  done
  if ((${#resources[@]} == 0)); then
    return
  fi
  local -a tags=(
    "Key=Name,Value=${BACKUP_NAME_PREFIX}"
    "Key=Case,Value=${BACKUP_TAG_CASE}"
    "Key=SourceInstanceId,Value=${instance_id}"
    "Key=CreatedBy,Value=automated-backup"
    "Key=CreatedOn,Value=${created_on}"
  )
  if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY RUN] Would tag resources (${resources[*]}) in $region with backup metadata."
  else
    aws ec2 create-tags --region "$region" --resources "${resources[@]}" --tags "${tags[@]}"
  fi
}

process_region() {
  local region="$1"
  shift || true
  local -a explicit_ids=()
  while (($#)); do
    [[ -n "$1" ]] && explicit_ids+=("$1")
    shift || true
  done
  local had_explicit=0
  if ((${#explicit_ids[@]} > 0)); then
    had_explicit=1
  fi

  local -a instance_ids=()
  local id
  for id in "${explicit_ids[@]}"; do
    if is_valid_instance_id "$id"; then
      instance_ids+=("$id")
    else
      warn "Skipping invalid instance ID '$id' for $region. Set array to () to auto-discover."
    fi
  done

  if ((had_explicit == 1 && ${#instance_ids[@]} == 0)); then
    warn "Explicit instance list for $region contained no valid IDs; skipping region."
    return
  fi

  if ((${#instance_ids[@]} == 0)); then
    log "Auto-discovering running instances in $region"
    while IFS= read -r id; do
      [[ -z "$id" || "$id" == "null" ]] && continue
      instance_ids+=("$id")
    done < <(aws ec2 describe-instances \
      --region "$region" \
      --filters Name=instance-state-name,Values=running \
      --query 'Reservations[].Instances[].InstanceId' \
      --output json | jq -r '.[]?')
  fi

  if ((${#instance_ids[@]} == 0)); then
    log "No instances to process in $region"
    return
  fi

  for id in "${instance_ids[@]}"; do
    process_instance "$region" "$id"
  done
}

process_instance() {
  local region="$1"
  local instance_id="$2"

  log "Processing instance $instance_id in $region"

  local instance_json
  if ! instance_json=$(aws ec2 describe-instances --region "$region" --instance-ids "$instance_id" --output json 2>/dev/null); then
    warn "Unable to describe instance $instance_id in $region; skipping."
    return
  fi

  local reservation_count
  reservation_count=$(jq -r '.Reservations | length' <<<"$instance_json")
  if [[ "$reservation_count" == "0" ]]; then
    warn "Instance $instance_id not found in $region (possibly terminated); skipping."
    return
  fi

  local instance_type subnet_id root_device availability_zone key_name iam_profile instance_name
  instance_type=$(jq -r '.Reservations[0].Instances[0].InstanceType' <<<"$instance_json")
  subnet_id=$(jq -r '.Reservations[0].Instances[0].SubnetId // empty' <<<"$instance_json")
  root_device=$(jq -r '.Reservations[0].Instances[0].RootDeviceName // empty' <<<"$instance_json")
  availability_zone=$(jq -r '.Reservations[0].Instances[0].Placement.AvailabilityZone // empty' <<<"$instance_json")
  key_name=$(jq -r '.Reservations[0].Instances[0].KeyName // empty' <<<"$instance_json")
  iam_profile=$(jq -r '.Reservations[0].Instances[0].IamInstanceProfile.Arn // empty' <<<"$instance_json")
  instance_name=$(jq -r '.Reservations[0].Instances[0].Tags[]? | select(.Key=="Name") | .Value' <<<"$instance_json")
  local security_groups_json
  security_groups_json=$(jq '[.Reservations[0].Instances[0].SecurityGroups[]?.GroupId]' <<<"$instance_json")

  local block_device_base volume_details_json
  block_device_base=$(jq '.Reservations[0].Instances[0].BlockDeviceMappings | map(select(.Ebs != null) | {device_name: .DeviceName, volume_id: .Ebs.VolumeId, delete_on_termination: (.Ebs.DeleteOnTermination // false)})' <<<"$instance_json")
  volume_details_json="$block_device_base"

  local volume_ids
  volume_ids=$(jq -r '.Reservations[0].Instances[0].BlockDeviceMappings | map(select(.Ebs != null) | .Ebs.VolumeId) | join(" ")' <<<"$instance_json")
  if [[ -n "$volume_ids" ]]; then
    local volume_json vols_json
    volume_json=$(aws ec2 describe-volumes --region "$region" --volume-ids $volume_ids --output json)
    vols_json=$(jq '.Volumes' <<<"$volume_json")
    volume_details_json=$(jq -n \
      --argjson base "$block_device_base" \
      --argjson vols "$vols_json" '
        $base
        | map(. as $bd | $bd + (
            ($vols[]? | select(.VolumeId == $bd.volume_id)) // {}
            | {
                volume_type: (.VolumeType // "gp3"),
                volume_size: (.Size // 0),
                encrypted: (.Encrypted // false),
                iops: (.Iops // null),
                throughput: (.Throughput // null)
              }
          ))
      ')
  fi

  local existing_images selected_image_json
  existing_images=$(aws ec2 describe-images \
    --region "$region" \
    --owners self \
    --filters Name=tag:SourceInstanceId,Values="$instance_id" Name=tag:Name,Values="$BACKUP_NAME_PREFIX" \
    --output json)
  selected_image_json=$(jq -c --arg today "$TODAY" '
    .Images
    | map(select([(.Tags // [])[] | select(.Key=="CreatedOn") | .Value | startswith($today)] | length > 0))
    | sort_by(.CreationDate)
    | last // empty
  ' <<<"$existing_images")

  local ami_id="" ami_name="" created_on_tag="" ami_creation_date=""
  local snapshot_ids=()

  if [[ -n "$selected_image_json" && "$selected_image_json" != "null" ]]; then
    ami_id=$(jq -r '.ImageId' <<<"$selected_image_json")
    ami_name=$(jq -r '.Name // ""' <<<"$selected_image_json")
    ami_creation_date=$(jq -r '.CreationDate // ""' <<<"$selected_image_json")
    created_on_tag=$(jq -r '(.Tags[]? | select(.Key=="CreatedOn") | .Value) // ""' <<<"$selected_image_json")
    if [[ -z "$created_on_tag" || "$created_on_tag" == "null" ]]; then
      created_on_tag=$(iso_timestamp)
      if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Existing AMI $ami_id lacks CreatedOn tag; would tag with ${created_on_tag}."
      else
        log "Existing AMI $ami_id missing CreatedOn tag; tagging with ${created_on_tag}."
        aws ec2 create-tags --region "$region" --resources "$ami_id" --tags "Key=CreatedOn,Value=${created_on_tag}"
      fi
    fi
    ((existing_count++))
    log "Reusing existing AMI $ami_id for $instance_id (CreatedOn=${created_on_tag})."
  else
    if [[ "$DRY_RUN" == "true" ]]; then
      log "[DRY RUN] Would create new AMI for $instance_id in $region (no backup tagged for today)."
      if [[ -n "$S3_BACKUP_BUCKET" ]]; then
        local s3_prefix="${S3_BACKUP_BUCKET%/}/${region}/${instance_id}"
        printf '\n[INFO] Data-only backup suggestions for %s (%s)\n' "$instance_id" "$region"
        printf '# ssh -i /path/to/key.pem ec2-user@<instance_ip> "sudo tar -czf /tmp/%s-var-www.tgz /var/www"\n' "$instance_id"
        printf '# scp -i /path/to/key.pem ec2-user@<instance_ip>:/tmp/%s-var-www.tgz ./\n' "$instance_id"
        printf '# aws s3 cp %s-var-www.tgz %s/var-www-%s.tgz\n' "$instance_id" "$s3_prefix" "$TODAY"
        printf '# aws s3 sync --storage-class STANDARD_IA /etc %s/etc/\n' "$s3_prefix"
        printf '# aws s3 sync /home/ec2-user %s/home-ec2-user/ --delete\n\n' "$s3_prefix"
      fi
      return
    fi
    local timestamp created_on
    timestamp=$(date -u +%F-%H%M%S)
    created_on=$(iso_timestamp)
    ami_name="${BACKUP_NAME_PREFIX}-${region}-${instance_id}-${timestamp}"
    log "Creating AMI $ami_name from $instance_id (no reboot)."
    local create_image_json
    create_image_json=$(aws ec2 create-image \
      --region "$region" \
      --instance-id "$instance_id" \
      --name "$ami_name" \
      --description "Automated backup for $instance_id on $created_on" \
      --no-reboot \
      --output json)
    ami_id=$(jq -r '.ImageId' <<<"$create_image_json")
    created_on_tag="$created_on"
    log "AMI request ${ami_id} submitted; waiting for availability."
    aws ec2 wait image-available --region "$region" --image-ids "$ami_id"
    selected_image_json=$(aws ec2 describe-images --region "$region" --image-ids "$ami_id" --output json | jq -c '.Images[0]')
    ami_creation_date=$(jq -r '.CreationDate // ""' <<<"$selected_image_json")
    ((created_count++))
  fi

  if [[ -z "$ami_id" ]]; then
    warn "Unable to determine AMI ID for $instance_id in $region; skipping manifest update."
    return
  fi

  if [[ -z "$ami_name" || "$ami_name" == "null" ]]; then
    ami_name="${BACKUP_NAME_PREFIX}-${region}-${instance_id}"
  fi
  if [[ -z "$ami_creation_date" || "$ami_creation_date" == "null" ]]; then
    ami_creation_date=$(jq -r '.CreationDate // ""' <<<"$selected_image_json")
  fi
  if [[ -z "$created_on_tag" || "$created_on_tag" == "null" ]]; then
    created_on_tag=$(iso_timestamp)
  fi

  snapshot_ids=()
  if [[ -n "$selected_image_json" && "$selected_image_json" != "null" ]]; then
    while IFS= read -r snap; do
      [[ -z "$snap" || "$snap" == "null" ]] && continue
      snapshot_ids+=("$snap")
    done < <(jq -r '.BlockDeviceMappings[]? | .Ebs.SnapshotId // empty' <<<"$selected_image_json")
  fi

  tag_resources "$region" "$created_on_tag" "$instance_id" "$ami_id" "${snapshot_ids[@]}"

  local archive_info_json='{}'
  if [[ -n "$ARCHIVE_COPY_REGION" ]]; then
    local archive_region="$ARCHIVE_COPY_REGION"
    local existing_copy selected_copy_json
    existing_copy=$(aws ec2 describe-images \
      --region "$archive_region" \
      --owners self \
      --filters Name=tag:SourceInstanceId,Values="$instance_id" Name=tag:Name,Values="$BACKUP_NAME_PREFIX" Name=tag:Case,Values="$BACKUP_TAG_CASE" \
      --output json)
    selected_copy_json=$(jq -c --arg created "$created_on_tag" '
      .Images
      | map(select([(.Tags // [])[] | select(.Key=="CreatedOn") | .Value == $created] | length > 0))
      | sort_by(.CreationDate)
      | last // empty
    ' <<<"$existing_copy")
    local archive_ami_id="" archive_name="" archive_creation=""
    local archive_snapshot_ids=()
    if [[ -n "$selected_copy_json" && "$selected_copy_json" != "null" ]]; then
      archive_ami_id=$(jq -r '.ImageId' <<<"$selected_copy_json")
      archive_name=$(jq -r '.Name // ""' <<<"$selected_copy_json")
      archive_creation=$(jq -r '.CreationDate // ""' <<<"$selected_copy_json")
      while IFS= read -r snap; do
        [[ -z "$snap" || "$snap" == "null" ]] && continue
        archive_snapshot_ids+=("$snap")
      done < <(jq -r '.BlockDeviceMappings[]? | .Ebs.SnapshotId // empty' <<<"$selected_copy_json")
      log "Reusing archive AMI $archive_ami_id in $archive_region for $instance_id."
      tag_resources "$archive_region" "$created_on_tag" "$instance_id" "$archive_ami_id" "${archive_snapshot_ids[@]}"
    elif [[ "$DRY_RUN" == "true" ]]; then
      log "[DRY RUN] Would copy AMI $ami_id to $archive_region."
    else
      archive_name="${ami_name}-${archive_region}"
      log "Copying AMI $ami_id to $archive_region as $archive_name."
      local copy_image_json
      copy_image_json=$(aws ec2 copy-image \
        --region "$archive_region" \
        --source-region "$region" \
        --source-image-id "$ami_id" \
        --name "$archive_name" \
        --description "Archive copy of $ami_id from $region on $created_on_tag" \
        --output json)
      archive_ami_id=$(jq -r '.ImageId' <<<"$copy_image_json")
      log "Waiting for archive AMI $archive_ami_id in $archive_region."
      aws ec2 wait image-available --region "$archive_region" --image-ids "$archive_ami_id"
      selected_copy_json=$(aws ec2 describe-images --region "$archive_region" --image-ids "$archive_ami_id" --output json | jq -c '.Images[0]')
      archive_name=$(jq -r '.Name // ""' <<<"$selected_copy_json")
      archive_creation=$(jq -r '.CreationDate // ""' <<<"$selected_copy_json")
      while IFS= read -r snap; do
        [[ -z "$snap" || "$snap" == "null" ]] && continue
        archive_snapshot_ids+=("$snap")
      done < <(jq -r '.BlockDeviceMappings[]? | .Ebs.SnapshotId // empty' <<<"$selected_copy_json")
      tag_resources "$archive_region" "$created_on_tag" "$instance_id" "$archive_ami_id" "${archive_snapshot_ids[@]}"
    fi

    if [[ "$DRY_RUN" == "false" && -n "$archive_ami_id" ]]; then
      local archive_snapshots_json
      archive_snapshots_json=$(to_json_array "${archive_snapshot_ids[@]}")
      archive_info_json=$(jq -n \
        --arg region "$archive_region" \
        --arg ami_id "$archive_ami_id" \
        --arg ami_name "$archive_name" \
        --arg creation "$archive_creation" \
        --arg created_on "$created_on_tag" \
        --argjson snaps "$archive_snapshots_json" \
        '{($region): {ami_id: $ami_id, ami_name: $ami_name, ami_creation_date: $creation, created_on_tag: $created_on, snapshot_ids: $snaps}}'
      )
    fi
  fi

  local s3_examples_json='[]'
  if [[ -n "$S3_BACKUP_BUCKET" ]]; then
    if [[ "$S3_BACKUP_BUCKET" != s3://* ]]; then
      warn "S3_BACKUP_BUCKET should be in the form s3://bucket[/prefix]; current value '${S3_BACKUP_BUCKET}'."
    fi
    local s3_prefix="${S3_BACKUP_BUCKET%/}/${region}/${instance_id}"
    s3_examples_json=$(jq -n \
      --arg prefix "$s3_prefix" \
      --arg id "$instance_id" \
      --arg date "$TODAY" \
      '[
        "# ssh -i /path/to/key.pem ec2-user@<instance_ip> \"sudo tar -czf /tmp/\($id)-var-www.tgz /var/www\"",
        "# scp -i /path/to/key.pem ec2-user@<instance_ip>:/tmp/\($id)-var-www.tgz ./",
        "# aws s3 cp \($id)-var-www.tgz \($prefix + "/var-www-" + $date + ".tgz")",
        "# aws s3 sync --storage-class STANDARD_IA /etc \($prefix + "/etc/")",
        "# aws s3 sync /home/ec2-user \($prefix + "/home-ec2-user/") --delete"
      ]')
    printf '\n[INFO] Data-only backup suggestions for %s (%s)\n' "$instance_id" "$region"
    printf '# ssh -i /path/to/key.pem ec2-user@<instance_ip> "sudo tar -czf /tmp/%s-var-www.tgz /var/www"\n' "$instance_id"
    printf '# scp -i /path/to/key.pem ec2-user@<instance_ip>:/tmp/%s-var-www.tgz ./\n' "$instance_id"
    printf '# aws s3 cp %s-var-www.tgz %s/var-www-%s.tgz\n' "$instance_id" "$s3_prefix" "$TODAY"
    printf '# aws s3 sync --storage-class STANDARD_IA /etc %s/etc/\n' "$s3_prefix"
    printf '# aws s3 sync /home/ec2-user %s/home-ec2-user/ --delete\n\n' "$s3_prefix"
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    return
  fi

  local snapshot_ids_json
  snapshot_ids_json=$(to_json_array "${snapshot_ids[@]}")
  local archive_json="${archive_info_json:-{}}"

  manifest_content=$(jq \
    --arg region "$region" \
    --arg instance "$instance_id" \
    --arg ami_id "$ami_id" \
    --arg ami_name "$ami_name" \
    --arg created_on "$created_on_tag" \
    --arg creation_date "$ami_creation_date" \
    --arg instance_type "$instance_type" \
    --arg subnet "$subnet_id" \
    --arg az "$availability_zone" \
    --arg root_device "$root_device" \
    --arg key_name "$key_name" \
    --arg iam_profile "$iam_profile" \
    --arg instance_name "$instance_name" \
    --argjson security_groups "$security_groups_json" \
    --argjson snapshots "$snapshot_ids_json" \
    --argjson block_devices "$volume_details_json" \
    --argjson archive_copies "$archive_json" \
    --argjson s3_examples "$s3_examples_json" \
    '
    . as $root
    | if has($region) then . else . + {($region): {}} end
    | .[$region] += {
        ($instance): {
          instance_id: $instance,
          instance_name: $instance_name,
          region: $region,
          availability_zone: $az,
          ami_id: $ami_id,
          ami_name: $ami_name,
          ami_creation_date: $creation_date,
          created_on_tag: $created_on,
          snapshot_ids: $snapshots,
          instance_type: $instance_type,
          subnet_id: $subnet,
          security_group_ids: $security_groups,
          iam_instance_profile_arn: $iam_profile,
          key_name: $key_name,
          root_device_name: $root_device,
          block_devices: $block_devices,
          archive_copies: $archive_copies,
          s3_sync_examples: $s3_examples
        }
      }
    ' <<<"$manifest_content")
}

main() {
  validate_prereqs

  if [[ "$DRY_RUN" != "true" && "$DRY_RUN" != "false" ]]; then
    die "DRY_RUN must be set to 'true' or 'false'."
  fi

  TODAY=$(date -u +%F)
  log "Backup run started (DRY_RUN=${DRY_RUN}) for case ${BACKUP_TAG_CASE}"

  if [[ "$DRY_RUN" == "false" ]]; then
    if [[ -f "$MANIFEST_PATH" ]]; then
      if ! manifest_content=$(cat "$MANIFEST_PATH"); then
        die "Failed to read existing manifest at ${MANIFEST_PATH}"
      fi
      [[ -z "$manifest_content" ]] && manifest_content='{}'
    else
      manifest_content='{}'
    fi
    tmp_manifest=$(mktemp)
  fi

  process_region "us-east-1" "${US_EAST_1_INSTANCE_IDS[@]}"
  process_region "ap-northeast-1" "${AP_NORTHEAST_1_INSTANCE_IDS[@]}"

  if [[ "$DRY_RUN" == "false" ]]; then
    printf '%s\n' "$manifest_content" | jq '.' >"$tmp_manifest"
    mv "$tmp_manifest" "$MANIFEST_PATH"
    log "Backup manifest updated at ${MANIFEST_PATH}"
    log "AMIs created this run: ${created_count}; existing reused: ${existing_count}"
  else
    log "DRY_RUN completed. Re-run with DRY_RUN=false to execute."
  fi
}

main "$@"
