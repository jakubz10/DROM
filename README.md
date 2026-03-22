       _______   _______    ______   __       __
      /       \ /       \  /      \ /  \     /  |
      $$$$$$$  |$$$$$$$  |/$$$$$$  |$$  \   /$$ |
      $$ |  $$ |$$ |__$$ |$$ |  $$ |$$$  \ /$$$ |
      $$ |  $$ |$$    $$< $$ |  $$ |$$$$  /$$$$ |
      $$ |  $$ |$$$$$$$  |$$ |  $$ |$$ $$ $$/$$ |
      $$ |__$$ |$$ |  $$ |$$ \__$$ |$$ |$$$/ $$ |
      $$    $$/ $$ |  $$ |$$    $$/ $$ | $/  $$ |
      $$$$$$$/  $$/   $$/  $$$$$$/  $$/      $$/


-----------------------------------------------------------------

DROM - fps 3D game that runs in Windows terminal.

>Retro like game inspired by DOOM that runs entirely in cmd.

-----------------------------------------------------------------

Main task:
> Defeat droms (enemy robots that try to eliminate you)
> Defeat endgame drom boss that appears after you eliminate all of the rooms from current level
> Beat 5 levels with increasing amount of droms, drom bosses and increasing size of map. After you beat all 5 levels you can still play in infinite mode.

-----------------------------------------------------------------

Game mechanics:
> Player attacks droms with gun you have.
> Gun has 16 ammo slots; you can carry additional 32 bullets.
> There is gun upgrade you can pick up that upgrades your gun and it deals more damage to droms.
> Player has 100hp and can slightly heal himself with medkits that appear all over map.
> Player can pick up ammo crates that contain 16 bullets each.
> Walls are destructible and player can shoot them down with gun.
> Drom boss can break through walls.

-----------------------------------------------------------------

Controls:
 >    W               Movement system
    A S D
 > LEFT / RIGHT       Rotate camera (arrows)
 > UP / DOWN          180 degree camera flip (arrows)
 > Q / E              Rotate camera alternative
 > SPACE              Shoot
 > R                  Reload
 > ESC / BACKSPACE    Quit

-----------------------------------------------------------------

Requirements:
 >Python 3.10+ on Windows (uses Win32 console APIs)
 > Make sure your terminal window is large enough -- the game adapts to terminal size automatically.

-----------------------------------------------------------------

JZ