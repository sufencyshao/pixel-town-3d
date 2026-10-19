# vr-cats

> 日本語のREADMEはこちらです: [README.ja.md](README.ja.md)

A simple WebXR demo that displays animated 3D animal models using Three.js.

## Demos

-   **Default Experience (Cat & Lion):** [https://code4fukui.github.io/vr-cats/](https://code4fukui.github.io/vr-cats/)
-   **Alternate Experience (Cat & Bear):** [https://code4fukui.github.io/vr-cats/#bear](https://code4fukui.github.io/vr-cats/#bear)

## Features

-   **WebXR Support:** View the scene in virtual reality with a compatible headset.
-   **Animated Models:** Utilizes animated GLTF models for lifelike movement.
-   **PC Controls:** Navigate the scene with mouse and keyboard on a desktop.
-   **Dynamic Content:** The second animal model can be switched from a lion to a bear by using a URL hash (`#bear`).

## Getting Started

To run this project locally, you'll need a web browser that supports WebXR.

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/code4fukui/vr-cats.git
    cd vr-cats
    ```

2.  **Start a local web server.**
    You can use any simple web server. For example, if you have Python installed:
    ```sh
    python -m http.server
    ```

3.  **Open in your browser:**
    -   Navigate to `http://localhost:8000`.
    -   To see the bear model, navigate to `http://localhost:8000/#bear`.

## 3D Models and Attribution

This project uses freely licensed 3D models from Sketchfab.

-   **Bicolor Cat** by [kenchoo](https://sketchfab.com/kenchoo), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
    -   [View on Sketchfab](https://sketchfab.com/3d-models/bicolor-cat-e623a618ca344a8393d7ba4d63ec23cf)

-   **Lion** by [kenchoo](https://sketchfab.com/kenchoo), licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
    -   [View on Sketchfab](https://sketchfab.com/3d-models/lion-61d687ca92dc4cafbd5e74e3be40d49d)

-   **Strong Bear** by [Pedro B. Goulart](https://sketchfab.com/Pebegou), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
    -   [View on Sketchfab](https://sketchfab.com/3d-models/strong-bear-1d1bb459a39a428282ce4cb46bdc3ed5)

## License

This project is licensed under the MIT License.