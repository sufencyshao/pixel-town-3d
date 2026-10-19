# Asset Credits

## Cat model — attribution required

**"Cat" by madtrollstudio** — licensed under
[Creative Commons Attribution 3.0 (CC BY 3.0)](https://creativecommons.org/licenses/by/3.0/),
via [Poly Pizza](https://poly.pizza/m/YvVobPlTlQ).

This is the one asset in the project that carries an attribution obligation.
The credit must stay in this file **and** remain visible in-game (it is shown
in the on-screen credit line) for any distribution, including commercial use.

## Public domain (CC0) — no attribution required

These are CC0 and carry no obligations; they are listed for provenance only.

- **Character models** — [Animated Men Pack](https://poly.pizza/bundle/Animated-Men-Pack-DAC9SDgMQT)
  by [Quaternius](https://quaternius.com/). CC0.
- **Furniture** — [Low Poly Household Items Pack](https://lowpolyassets.itch.io/low-poly-household-item-pack)
  by LowPolyAssets (Edward Lunn). CC0. *Identified by pack name and model count
  (126 FBX); if you know it to be a different pack, update this entry.*
- **Textures** — [Poly Haven](https://polyhaven.com/): `plank_flooring_03`,
  `painted_plaster_wall`, `interior_tiles`. CC0.
- **Cat meow sounds** — [BigSoundBank](https://bigsoundbank.com/) by Joseph
  Sardin ("Little meow of a cat" #1 and #9). CC0 / public-domain equivalent.
- **"Found" purr sound** — [Cat Purr](https://bigsoundbank.com/detail-0436-cat-purr.html)
  by Joseph Sardin, BigSoundBank. CC0. Converted from the source MP3 to WAV with
  [PyAV](https://pyav.org/) (Ursina/Panda3D only load `.ogg`/`.wav`).

## Asset pipeline notes

- Furniture arrived as `.fbx`, which Panda3D cannot load. All 126 models were
  batch-converted to `.glb` with headless Blender.
- The Quaternius characters ship rigged and animated, but Panda3D's skinning
  pipeline mangles these particular rigs (the mesh renders as exploded
  triangles under both `panda3d-gltf` and `gltf2bam`). The walk cycle is
  therefore **pre-baked into 8 static posed meshes** plus an idle pose, which
  the game flipbooks at runtime. See `assets/characters/player/`.
