import React, { useEffect, useState } from 'react';
import './Vote.css';

const VoteButtons = ({
  turnId,
  conversationId,
  initialScore = 0,
  initialUserVote = 0,
  onVoteChange,
}) => {
  const [score, setScore] = useState(initialScore);
  const [userVote, setUserVote] = useState(initialUserVote);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setScore(initialScore);
  }, [initialScore]);

  useEffect(() => {
    setUserVote(initialUserVote);
  }, [initialUserVote]);

  const sendVote = async (nextVote) => {
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      const res = await fetch('/api/vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          turn_id: turnId,
          conversation_id: conversationId,
          vote: nextVote,
        }),
      });

      if (!res.ok) {
        throw new Error('Vote request failed');
      }

      setScore((prev) => prev - userVote + nextVote);
      setUserVote(nextVote);

      if (onVoteChange) {
        onVoteChange();
      }
    } catch (error) {
      console.error('Unable to submit vote:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="vote-container">
      <button
        type="button"
        className={userVote === 1 ? 'up active' : 'up'}
        onClick={() => sendVote(userVote === 1 ? 0 : 1)}
        disabled={isSubmitting}
        aria-label="Upvote turn"
      >
        ▲
      </button>

      <div className="score">{score}</div>

      <button
        type="button"
        className={userVote === -1 ? 'down active' : 'down'}
        onClick={() => sendVote(userVote === -1 ? 0 : -1)}
        disabled={isSubmitting}
        aria-label="Downvote turn"
      >
        ▼
      </button>
    </div>
  );
};

export default VoteButtons;
