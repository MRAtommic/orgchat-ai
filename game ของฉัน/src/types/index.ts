/* ========================================================
    Happy Farm 2D - TypeScript Types Barrel & Window Declaration
   ======================================================== */

export * from './items';
export * from './entities';
export * from './game';

declare global {
  interface Window {
    Game: any;
    Auth: any;
    SoundEngine: any;
    SPRITES: any;
    google: any;
  }
}
