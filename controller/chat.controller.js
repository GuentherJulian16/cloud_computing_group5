const Chat = require("../models/chats.js");
const Message = require("../models/messages.js");

exports.findAll = (req, res) => {
  Chat.getAll((err, data) => {
    if (err)
      res.status(500).send({ message: err.message || "Some error occurred while retrieving users." });
    else 
      res.send(data);
  });
};

exports.create = (req, res) => {
  if (!req.body) {
    res.status(400).send({status:0, message: "Content can not be empty!" });
  }

  const chat = new Chat({
    name: req.body.name,
    description: req.body.description,
    creatorId: req.session.user.id
  });

  Chat.create(chat, (err, data) => {
    if (err) {
      res.status(500).send({ status:0, message: err.message || "Some error occurred while creating the User." });
    } else { 
      res.status(200).send({ status: 1, id: data.id })
    }
  });
}

exports.show = (req, res) => {
  if(!req.session.user) {
    res.redirect('/')
  } else {
    Chat.getChatById(req.params.id, (err, data) => {
      if(!data || data.length == 0) {
        res.redirect("/");
      } else {
        var time = new Date().toISOString().slice(0, 19).replace('T', ' ');
        var chat = data[0];
        var message = new Message({
          userId: 0,
          chatId: req.params.id,
          message: req.session.user.username + " hat den Chat betreten",
          time_created: time
        });

        Message.create(message, (err, data) => {
          res.render('chat', {
            session: req.session,
            chat: chat,
            timeChatJoined: time
          });
        });
      }
    })
  }
}

exports.getChatById = (req, res) => {
  Chat.getChatById(req.id, (err, data) => {
    if (err) {
      res.status(500).send({ status:0, message: err.message || "Some error occurred." });
    } else { 
      res.status(200).send({ status: 1, chat: data })
    }
  });
}
