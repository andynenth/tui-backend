// frontend/main.js

import { Application } from 'pixi.js';
import '@pixi/layout';
import { SceneManager } from './SceneManager.js';
import { StartScene } from './scenes/StartScene.js';
// import './test.js';


(async () => {
  const app = new Application();
  await app.init({ width: 540, height: 960, background: '#1e1e2e' });
  document.body.appendChild(app.canvas);

  app.stage.layout = {
    width: app.screen.width,
    height: app.screen.height,
    justifyContent: 'center',
    alignItems: 'center',
  };

  const sceneManager = new SceneManager(app);

  const startScene = new StartScene((playerName) => {
    console.log('✅ Name submitted:', playerName);
    // 👉 ต่อไปยัง LobbyScene
    // const lobbyScene = new LobbyScene(...);
    // sceneManager.changeScene(lobbyScene);
  });

  sceneManager.changeScene(startScene);
})();
