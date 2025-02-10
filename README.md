<h1 align="center">Multi-Agent Wumpus-World</h1>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#agent-types">Agent Types</a>
    </li>
  </ol>
</details>

## About the project
is an extension of the Wumpus game by a multi-agent environment approach with
- communication between agents through a channel object
- different classes of agents with different focuses
- A*-algorithm as the traversal algorithm through the map

### Build with
[![Python][Python]][Python-url]

## Agent Types:
<ol>
  <li>Hunter</li>
  <ul>
    <li>can kill wumpi with an arrow whose range is his von neumann neighbourhood</li>
    <li>arrow replenishes every 32 rounds</li>
    <li>prioritizes killing wumpi</li>
  </ul>
  <li>Cartograph</li>
  <ul>
    <li>has a map of all the tiles with condition "WALL" (ref)</li>
    <li>prioritizes map progress</li>
  </ul>
  <li>Knight</li>
  <ul>
    <li>can kill wumpi by standing on its inhabited tile every 32 rounds</li>
    <li>if the knight steps on a wumpi without waiting for the replenish, it dies</li>
    <li>prioritizes gold and killing wumpi</li>
  </ul>
  <li>BWL-Student</li>
  <ul>
    <li>can sniff out gold tiles through a radius of 5 tiles</li>
    <li>prioritizes gold</li>
  </ul>
</ol>

## Map


<!-- MARKDOWN LINKS & IMAGES -->
[Python]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://www.python.org/
