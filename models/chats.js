const sql = require("./db.js");

// constructor
const Chat = function(chat) {
  this.name = chat.name;
  this.description = chat.description;
  this.creatorId = chat.creatorId;
};

Chat.create = (newChat, result) => {
  sql.query("INSERT INTO chats SET ?", newChat, (err, res) => {
    if (err) {
      console.log("error: ", err);
      result(err, null);
      return;
    }

    console.log("created chat: ", { id: res.insertId, ...newChat });
    result(null, { id: res.insertId, ...newChat });
  });
};

Chat.getAll = (result) => {
    sql.query("SELECT * FROM chats", (err, res) => {
      if (err) {
        console.log("error: ", err);
        result(null, err);
        return;
      }
  
      console.log("chats: ", res);
      result(null, res);
    });
};

Chat.getChatById = (id, result) => {
  sql.query("SELECT * FROM chats where id = ?", [id],  (err, res) => {
    if (err) {
      console.log("error: ", err);
      result(null, err);
      return;
    }

    console.log("chat: ", res);
    result(null, res);
  });
};

module.exports = Chat