import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <main className="title-slide">
      <header className="title-slide-header">
        <Link className="title-slide-brand" to="/">
          ai student advisor
        </Link>
        <nav className="title-slide-actions" aria-label="Account actions">
          <Link to="/login">Login</Link>
          <Link to="/signup">Signup</Link>
        </nav>
      </header>

      <section className="title-slide-content" aria-labelledby="homepage-title">
        <h1 id="homepage-title">ai student advisor</h1>
        <p>chatbot and other tools meant to assist with academic advising at Purdue.</p>
      </section>
    </main>
  );
};

export default Home;
