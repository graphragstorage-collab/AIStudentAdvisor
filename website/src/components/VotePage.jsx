import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import VoteButtons from './Vote';
import './VotePage.css';

const VotePage = () => {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [selectedConversationId, setSelectedConversationId] = useState('');
  const [turns, setTurns] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingTurns, setIsLoadingTurns] = useState(false);
  const [error, setError] = useState('');

  const loadConversations = useCallback(async ({ showLoading = false } = {}) => {
    if (showLoading) {
      setIsLoadingConversations(true);
    }

    try {
      const response = await fetch('/api/my/conversations', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Could not load conversations');
      }

      const data = await response.json();
      setConversations(data);

      if (data.length === 0) {
        setSelectedConversationId('');
      } else {
        setSelectedConversationId((currentValue) => {
          const existing = data.find(
            (conversation) => String(conversation.Conversation_id) === String(currentValue)
          );
          return existing ? existing.Conversation_id : data[0].Conversation_id;
        });
      }

      return data;
    } catch (loadError) {
      console.error('Unable to load conversations:', loadError);
      setError('Could not load conversations right now.');
      return [];
    } finally {
      if (showLoading) {
        setIsLoadingConversations(false);
      }
    }
  }, []);

  const loadTurns = useCallback(async (conversationId, { showLoading = false } = {}) => {
    if (!conversationId) {
      setTurns([]);
      return;
    }

    if (showLoading) {
      setIsLoadingTurns(true);
    }

    try {
      const turnsResponse = await fetch(`/api/my/conversation/${conversationId}`, {
        credentials: 'include',
      });

      if (!turnsResponse.ok) {
        throw new Error('Could not load turns');
      }

      const turnData = await turnsResponse.json();
      const enrichedTurns = await Promise.all(
        turnData.map(async (turn) => {
          const voteResponse = await fetch(
            `/api/votes/${turn.Turn_id}?conversation_id=${conversationId}`,
            { credentials: 'include' }
          );

          if (!voteResponse.ok) {
            throw new Error(`Could not load votes for turn ${turn.Turn_id}`);
          }

          const voteData = await voteResponse.json();

          return {
            ...turn,
            score: voteData.score ?? 0,
            userVote: voteData.user_vote ?? 0,
          };
        })
      );

      setTurns(enrichedTurns);
      setError('');
    } catch (loadError) {
      console.error('Unable to load turns:', loadError);
      setError('Could not load the turns for this conversation.');
      setTurns([]);
    } finally {
      if (showLoading) {
        setIsLoadingTurns(false);
      }
    }
  }, []);

  const refreshVoteData = useCallback(async ({ showLoading = false } = {}) => {
    const latestConversations = await loadConversations({ showLoading });
    const currentConversationId =
      latestConversations.find(
        (conversation) =>
          String(conversation.Conversation_id) === String(selectedConversationId)
      )?.Conversation_id ??
      (latestConversations[0]?.Conversation_id || '');

    if (currentConversationId) {
      await loadTurns(currentConversationId, { showLoading });
    } else {
      setTurns([]);
    }
  }, [loadConversations, loadTurns, selectedConversationId]);

  useEffect(() => {
    refreshVoteData({ showLoading: true });
  }, [refreshVoteData]);

  useEffect(() => {
    if (!selectedConversationId) {
      setTurns([]);
      return;
    }

    loadTurns(selectedConversationId, { showLoading: true });
  }, [loadTurns, selectedConversationId]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      refreshVoteData();
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [refreshVoteData]);

  const handleNewChat = async () => {
    try {
      const response = await fetch('/api/my/conversations', {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Could not create conversation');
      }

      const data = await response.json();
      navigate('/chat', { state: { conversationId: data.conversation_id } });
    } catch (creationError) {
      console.error('Unable to create conversation:', creationError);
      setError('Could not start a new chat right now.');
    }
  };

  return (
    <div className="vote-page">
      <div className="vote-page-header">
        <div>
          <h1>Turn Voting</h1>
          <p>Review your turns, vote on responses, or start a fresh conversation.</p>
        </div>

        <div className="vote-page-actions">
          <button type="button" className="new-chat-btn" onClick={handleNewChat}>
            New Chat
          </button>
          <button
            type="button"
            className="back-btn"
            onClick={() => navigate('/chat')}
          >
            Back to Chat
          </button>
        </div>
      </div>

      <div className="vote-toolbar">
        <label htmlFor="conversation-select">Conversation</label>
        <select
          id="conversation-select"
          value={selectedConversationId}
          onChange={(event) => setSelectedConversationId(event.target.value)}
          disabled={isLoadingConversations || conversations.length === 0}
        >
          {conversations.length === 0 ? (
            <option value="">No conversations found</option>
          ) : (
            conversations.map((conversation) => (
              <option
                key={conversation.Conversation_id}
                value={conversation.Conversation_id}
              >
                Conversation {conversation.Conversation_id}
              </option>
            ))
          )}
        </select>
      </div>

      {error ? <div className="vote-status error">{error}</div> : null}
      {isLoadingConversations || isLoadingTurns ? (
        <div className="vote-status">Loading turns...</div>
      ) : null}

      {!isLoadingConversations && !isLoadingTurns && turns.length === 0 && !error ? (
        <div className="vote-status">No turns found for this conversation.</div>
      ) : null}

      <div className="vote-feed">
        {turns.map((turn) => (
          <div className="vote-card" key={`${turn.Conversation_id}-${turn.Turn_id}`}>
            <div className="vote-card-content">
              <div className="turn-id">Turn #{turn.Turn_id}</div>
              <div className="turn-q">Q: {turn.question}</div>
              <div className="turn-a">A: {turn.answer}</div>
            </div>

            <VoteButtons
              turnId={turn.Turn_id}
              conversationId={turn.Conversation_id}
              initialScore={turn.score}
              initialUserVote={turn.userVote}
              onVoteChange={() => refreshVoteData()}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default VotePage;
