/* ========================================================
    Happy Farm 2D (Stardew Style) - Main Entry Point (Vite)
   ======================================================== */

// 1. Stylesheet
import '../style.css';

// 2. Types
export * from './types';

// 3. Game Data Configuration
export * from './data/gamedata';

// 4. Subsystems
import { SoundEngine } from './audio/soundEngine';
import { SPRITES } from './sprites/sprites';
import { Auth } from './auth/authManager';
import { Game } from './engine/game';
import { Multiplayer } from './network/multiplayer';
import { VOLCANO_FORGE_RECIPES, WORLD_ITEMS, PIRATE_SHOP_ITEMS } from './data/gamedata';

// Bind to window global scope for HTML onclick handlers and cross-subsystem interop
declare global {
  interface Window {
    Game: any;
    Auth: any;
    SoundEngine: any;
    SPRITES: any;
    Multiplayer: any;
    VOLCANO_FORGE_RECIPES: any;
    WORLD_ITEMS: any;
    PIRATE_SHOP_ITEMS: any;
  }
}

(window as any).Game = Game;
(window as any).Auth = Auth;
(window as any).SoundEngine = SoundEngine;
(window as any).SPRITES = SPRITES;
(window as any).Multiplayer = Multiplayer;
(window as any).VOLCANO_FORGE_RECIPES = VOLCANO_FORGE_RECIPES;
(window as any).WORLD_ITEMS = WORLD_ITEMS;
(window as any).PIRATE_SHOP_ITEMS = PIRATE_SHOP_ITEMS;

// Close modal when clicking outside on the backdrop
document.addEventListener('click', (e) => {
  const target = e.target as HTMLElement;
  if (target && target.classList && target.classList.contains('modal-overlay')) {
    if ((window as any).Game && typeof (window as any).Game.closeAllModals === 'function') {
      (window as any).Game.closeAllModals();
    }
  }
});

export { SoundEngine, SPRITES, Auth, Game, Multiplayer };

// Console banner for developers
console.log(
  '%c ฟาร์มสุขใจ - Happy Farm 2D %c[TypeScript + Vite + Multiplayer]%c\nLoaded modular game engine successfully!',
  'background: #2b180a; color: #fef3c7; font-size: 14px; font-weight: bold; padding: 4px 8px; border-radius: 4px;',
  'background: #3178c6; color: #fff; font-size: 12px; font-weight: bold; padding: 4px 6px; border-radius: 4px; margin-left: 4px;',
  'color: #10b981; font-weight: 600;'
);
