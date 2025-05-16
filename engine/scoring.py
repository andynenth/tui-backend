# engine/scoring.py

def calculate_score(declared: int, actual: int) -> int:
    """
    คำนวณคะแนนของผู้เล่นจากค่าประกาศและผลจริง
    """
    if declared == 0:
        if actual == 0:
            return 3  # สำเร็จ: ประกาศ 0 แล้วไม่กินอะไร → ได้โบนัส +3
        else:
            return -actual  # ล้มเหลว: กินได้แต่ไม่ควร → ติดลบเท่าที่กิน
    else:
        if actual == declared:
            return declared + 5  # สำเร็จตรงเป๊ะ → ได้แต้ม +5 โบนัส
        else:
            return -abs(declared - actual)  # ผิด → ติดลบเท่ากับส่วนต่าง
