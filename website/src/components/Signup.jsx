import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Auth.css';

const Signup = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirm: ''
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirm) {
      setError('Passwords do not match.');
      return;
    }

    const formBody = new URLSearchParams();
    formBody.append('username', formData.username);
    formBody.append('password', formData.password);
    formBody.append('confirm', formData.confirm);

    try {
      const response = await fetch('/api/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formBody,
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok && data.success) {
          navigate('/login');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h2>Create Account</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <input
            name="username"
            placeholder="Username"
            value={formData.username}
            onChange={handleChange}
            required
          />
          <input
            name="password"
            placeholder="Password (no commas)"
            type="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
          <input
            name="confirm"
            placeholder="Confirm Password"
            type="password"
            value={formData.confirm}
            onChange={handleChange}
            required
          />
          <button type="submit">Register</button>
        </form>
      </div>
    </div>
  );
};

export default Signup;
