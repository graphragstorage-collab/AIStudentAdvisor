import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
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
          <Route path="/" element={<Navigate to="/login" />} />
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
