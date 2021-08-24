const sql = require("./db.js");

// constructor
const Message = function(message) {
  this.userId = message.userId;
  this.chatId = message.chatId;
  this.message = message.message;
  this.time_created = message.time_created;
};

Message.create = (newMessage, result) => {
  sql.query("INSERT INTO messages SET ?", newMessage, (err, res) => {
    if (err) {
      console.log("error: ", err);
      result(err, null);
      return;
    }

    result(null, res);
    return;
  });
};

Message.getAllByChat = (chatId, result) => {
  sql.query("SELECT * FROM messages WHERE chatId = ?", [chatId], (err, res) => {
    if (err) {
      console.log("error: ", err);
      result(err, null);
      return;
    }

    if (res.length) {
      result(null, res);
      return;
    }

    result({ kind: "not_found" }, null);
  });
};

Message.getAllByChatAndTime = (chatId, time, result) => {
  sql.query("SELECT m.id, m.message, m.time_created, u.username FROM messages m LEFT JOIN users u ON m.userId = u.id WHERE chatId = ? AND time_created >= ?", [chatId, time], (err, res) => {
    if (err) {
      console.log("error: ", err);
      result(err, null);
      return;
    }

    if (res.length) {
      console.log("found message: " + res.length)
      result(null, res);
      return;
    }

    result({ kind: "not_found" }, null);
  });
};

module.exports = Message