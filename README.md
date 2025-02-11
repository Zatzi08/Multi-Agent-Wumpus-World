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
is an extension of the [wumpus game](https://de.wikipedia.org/wiki/Wumpus-Welt) by a multi-agent environment approach with
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
<table>
  <tr>
    <td><img src="media/wumpusMap.png" width="500" height="500"/>
    <td>🟥 <strong>Red:</strong> Wumpus<br>🟩 <strong>Green:</strong> Stench<br>🟦 <strong>Blue:</strong> Pit<br>🟦 <strong>Light Blue:</strong> Breeze<br>🟨 <strong>Yellow:</strong> Shiny<br>🟠 <strong>Orange:</strong> Agent
      </ul>
    </td>
  </tr>
</table>

### Quick explanation of the world
<ul>
  <li>a wumpus is always surrounded by stenches</li>
  <li>a pit is always surrounded by breezes</li>
  <li>stepping on a wumpus tile or a pit tile leads to the agent dying</li>
  <li>collecting gold by stepping on it stores it inside the agents inventory</li>
</ul>

## Knowledge Base
### Possible states of a field (in der Wissensbasis)

### Possible states of a field (in der Wissensbasis)

<table>
  <tr>
    <th rowspan="2">Allowed additional states</th>
    <th colspan="7">Field states that are mutually exclusive</th>
  </tr>
  <tr>
    <th>Safe</th>
    <th>Wumpus</th>
    <th>Pit</th>
    <th>Wall</th>
    <th>Unknown (1)</th>
    <th>Unknown (2)</th>
    <th>Unknown (3)</th>
  </tr>
  <tr>
    <td><strong>Stench</strong></td>
    <td>🟩</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟩</td><td>🟥</td><td>🟥</td>
  </tr>
  <tr>
    <td><strong>Breeze</strong></td>
    <td>🟩</td><td>🟩</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟩</td><td>🟥</td>
  </tr>
  <tr>
    <td><strong>Shiny</strong></td>
    <td>🟩</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟥</td>
  </tr>
  <tr>
    <td><strong>◊Wumpus</strong></td>
    <td>🟥</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟩</td><td>🟩</td>
  </tr>
  <tr>
    <td><strong>◊Pit</strong></td>
    <td>🟥</td><td>🟥</td><td>🟥</td><td>🟥</td><td>🟩</td><td>🟥</td><td>🟩</td>
  </tr>
</table>
<i>Note: the logical ◊ operator stands for a possibility</i>

<ul>
  <li>the knowledge base of an agent uses predicate logic and modal logic approaches to deduce new from old knowledge through predictions and re-predictions</li>
  <li>Unknown (1|2|3) means that the state of the tile condition is to be deduced through further knowledge</li>
  <li>predictions are marked accordingly in the map through pink for "◊Wumpus" and teal for "◊Pit"</li>
</ul>


<!-- MARKDOWN LINKS & IMAGES -->
[Python]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://www.python.org/
