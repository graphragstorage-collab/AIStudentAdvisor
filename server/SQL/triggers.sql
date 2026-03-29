DELIMITER $$

CREATE TRIGGER IF NOT EXISTS ensure_user_exists
BEFORE INSERT ON Conversation
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM User WHERE User_id = NEW.User_id
    ) THEN
        INSERT INTO User (User_id, Username)
        VALUES (NEW.User_id, CONCAT('User_', NEW.User_id));
    END IF;
END$$

DELIMITER ;
