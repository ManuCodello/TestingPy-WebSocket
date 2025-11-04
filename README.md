<h1>🧪 TestingPy-WebSocket</h1>

<p align="center">
  <strong>A real-time chat application demonstrating a full testing strategy for Python, Asyncio, and WebSockets.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue.svg?style=for-the-badge&logo=python" alt="Python 3.x">
  <img src="https://img.shields.io/badge/Async-Asyncio-purple?style=for-the-badge" alt="Asyncio">
  <img src="https://img.shields.io/badge/Library-WebSockets-blueviolet?style=for-the-badge" alt="WebSockets">
  <img src="https://img.shields.io/badge/Testing-Pytest-green?style=for-the-badge&logo=pytest" alt="Pytest">
  <img src="https://img.shields.io/badge/GUI-Tkinter-orange?style=for-the-badge" alt="Tkinter">
</p>

<h2>Project Overview</h2>

<p>This project is a high-quality example of a modern, asynchronous chat application in Python. It uses <code>asyncio</code> and the <code>websockets</code> library for efficient, non-blocking communication, and features a simple <code>tkinter</code> GUI client.</p>

<p>The primary focus of this repository is to demonstrate a robust and comprehensive <strong>testing strategy</strong> for an asynchronous, networked application. It includes clear examples of unit tests, mocked server tests, and full end-to-end integration tests.</p>

<hr>

<h2>Features</h2>

<ul>
  <li><strong>Asynchronous Server:</strong> The server (<code>server.py</code>) is built with <code>asyncio</code> and <code>websockets</code>, capable of handling numerous concurrent clients efficiently.</li>
  <li><strong>GUI Client:</strong> A functional chat client (<code>client.py</code>) built with <code>tkinter</code> that runs its network I/O in a separate <code>asyncio</code> event loop.</li>
  <li><strong>Clear Protocol:</strong> A simple, JSON-based messaging protocol is defined in <code>protocol.py</code>, decoupling the message format from the server/client logic.</li>
  <li><strong>Clean Architecture:</strong> The project is well-structured, with clear separation of concerns between the server, client, protocol, and entry point (<code>main.py</code>).</li>
</ul>

<h3>🧪 A Comprehensive Testing Strategy</h3>
<p>This project's main strength is its test suite, which is divided into three levels:</p>
<ol>
  <li><strong>Unit Tests (<code>test_protocol.py</code>):</strong>
    These tests check the pure functions in <code>protocol.py</code> (<code>parse_message</code>, <code>create_message</code>) to ensure they correctly serialize and deserialize JSON messages.</li>
  
  <li><strong>Mocked Server Tests (<code>test_server.py</code>):</strong>
    These tests check the <code>Server</code> class logic in isolation. They use <code>unittest.mock</code> to create "fake" WebSocket connections, allowing the test to verify that the server correctly registers clients, unregisters clients, and broadcasts messages without needing a real network.</li>
  
  <li><strong>Full Integration Tests (<code>test_integration_chat.py</code>):</strong>
    These are end-to-end tests that verify the *entire system*. Using <code>pytest_asyncio</code>, the tests start a <strong>real server</strong> (via the <code>live_server</code> fixture in <code>conftest.py</code>), connect multiple <strong>real clients</strong> to it, and then simulate sending and receiving messages to confirm the whole application works together as expected.</li>
</ol>

<hr>

<h2>How to Run the Application</h2>

<h3>Prerequisites</h3>
<ul>
  <li>Python 3.7+</li>
  <li>Required libraries: <code>websockets</code></li>
</ul>

<pre><code>pip install websockets
</code></pre>

<h3>1. Run the Server</h3>
<p>Open a terminal and run <code>main.py</code>. This starts the WebSocket server.</p>
<pre><code>python main.py
</code></pre>
<blockquote>
  <p>Server started on ws://localhost:8765</p>
</blockquote>

<h3>2. Run the Client(s)</h3>
<p>Open one or more new terminal windows and run <code>client.py</code>. Each instance will open a new GUI chat window.</p>
<pre><code>python client.py
</code></pre>
<p>You can now type messages in any client window, and they will be broadcast to all other open clients.</p>

<hr>

<h2>How to Run the Tests</h2>

<h3>Prerequisites</h3>
<ul>
  <li>Required testing libraries: <code>pytest</code>, <code>pytest-asyncio</code></li>
</ul>
<pre><code>pip install pytest pytest-asyncio
</code></pre>

<h3>Run the Test Suite</h3>
<p>Simply run <code>pytest</code> from the root directory of the project.</p>
<pre><code>pytest
</code></pre>
<p>This will automatically discover and run all unit, mocked, and integration tests and provide a coverage report.</p>
