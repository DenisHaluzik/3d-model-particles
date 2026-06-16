# 3D Model Particle System (Octopus)

Interaktivní 3D webová aplikace vytvořená v knihovně **Three.js**, která převádí vertexy 3D modelu (chobotnice) na dynamický částicový systém (particle system) reagující na myš.

## 🚀 Vlastnosti projektu
- **Převod 3D modelu na částice:** Načtení 3D sítě z modelu (GLTF/GLB) a převedení jejích vrcholů (vertexů) na samostatné částice.
- **Interaktivní fyzika:** Částice reagují na pohyb kurzoru myši – odtlačují se od něj a pomocí pružinové fyziky (spring physics) se hladce vrací na své původní místo, čímž drží tvar chobotnice.
- **GPU zrychlení:** Využití vlastních shaderů (Vertex a Fragment Shader) přes `ShaderMaterial` pro plynulý běh a vykreslování desítek tisíc částic na grafické kartě.
- **Plynulý pohyb:** Jemná rotace a vlnění částic vytváří organický dojem plování ve vodě.
- **Plně autonomní:** Aplikace je zabalená do jednoho souboru (`index.html`) s integrovaným 3D modelem zakódovaným v Base64 pro okamžité spuštění bez nutnosti stahování externích souborů.

## 💻 Použité technologie
- **HTML5 & CSS3** – struktura a design rozhraní.
- **JavaScript (ES6+)** – aplikační logika a fyzikální výpočty.
- **Three.js** – vykreslování 3D scény, správa kamer, světel a načítání modelů.
- **GLSL Shaders** – shaderový kód pro efektivní renderování částic na GPU.
