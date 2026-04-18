-- Order matters because of FK dependencies

CREATE TABLE IF NOT EXISTS User (
    User_id INT PRIMARY KEY,
    Username VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Conversation (
    Conversation_id INT PRIMARY KEY,
    User_id INT,
    FOREIGN KEY (User_id) REFERENCES User(User_id)
);

CREATE TABLE IF NOT EXISTS Turn (
    Turn_id INT,
    Conversation_id INT,
    question TEXT,
    answer TEXT,
    rating INT DEFAULT 0,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (Turn_id, Conversation_id),
    FOREIGN KEY (Conversation_id) REFERENCES Conversation(Conversation_id)
);

CREATE TABLE IF NOT EXISTS Vote (
    Turn_id INT,
    Conversation_id INT,
    User_id INT,
    vote INT,
    PRIMARY KEY (Turn_id, Conversation_id, User_id),
    FOREIGN KEY (Turn_id, Conversation_id)
        REFERENCES Turn(Turn_id, Conversation_id)
);

CREATE TABLE IF NOT EXISTS Document (
    Document_id INT PRIMARY KEY,
    text TEXT
);

CREATE TABLE IF NOT EXISTS Retrieval (
    Turn_id INT,
    Conversation_id INT,
    Document_id INT,
    PRIMARY KEY (Turn_id, Conversation_id, Document_id),
    FOREIGN KEY (Turn_id, Conversation_id)
        REFERENCES Turn(Turn_id, Conversation_id),
    FOREIGN KEY (Conversation_id)
        REFERENCES Conversation(Conversation_id),
    FOREIGN KEY (Document_id)
        REFERENCES Document(Document_id)
);
