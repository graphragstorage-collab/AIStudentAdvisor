import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import Login from './components/Login';
import Signup from './components/Signup';
import Chat from './components/Chat';
import VotePage from './components/VotePage';
import CoursePlanner from './components/CoursePlanner';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/vote" element={<VotePage />} />
          <Route path="/planner" element={<CoursePlanner />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
