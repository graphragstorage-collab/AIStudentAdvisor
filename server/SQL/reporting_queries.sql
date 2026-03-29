-- conversations summary
SELECT 
    c.Conversation_id,
    u.Username,
    MAX(t.time) AS latest_time,
    AVG(t.rating) AS avg_rating
FROM Conversation c
JOIN User u ON c.User_id = u.User_id
LEFT JOIN Turn t ON c.Conversation_id = t.Conversation_id
GROUP BY c.Conversation_id, u.Username;


-- turns for a conversation
SELECT 
    Turn_id,
    question,
    answer,
    rating,
    time
FROM Turn
WHERE Conversation_id = %s
ORDER BY time ASC;


-- documents + aggregate rating
SELECT 
    d.Document_id,
    d.text,
    COALESCE(SUM(t2.rating), 0) AS total_rating
FROM Retrieval r
JOIN Document d ON r.Document_id = d.Document_id
LEFT JOIN Retrieval r2 ON r2.Document_id = d.Document_id
LEFT JOIN Turn t2 
    ON r2.Turn_id = t2.Turn_id 
    AND r2.Conversation_id = t2.Conversation_id
WHERE r.Turn_id = %s AND r.Conversation_id = %s
GROUP BY d.Document_id;


-- user filter
SELECT 
    c.Conversation_id,
    u.Username,
    MAX(t.time) AS latest_time,
    AVG(t.rating) AS avg_rating
FROM Conversation c
JOIN User u ON c.User_id = u.User_id
LEFT JOIN Turn t ON c.Conversation_id = t.Conversation_id
WHERE u.Username LIKE %s
GROUP BY c.Conversation_id, u.Username;
