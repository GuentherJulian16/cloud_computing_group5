const Chat = require("../models/chats.js");
const Message = require("../models/messages.js");

exports.getByChat = (req, res) => {
  var time = new Date(parseInt(req.params.time));
  Message.getAllByChatAndTime(parseInt(req.params.chatId), time, (err, data) => {
    console.log(data)
    if (data) {
      res.status(200).send({ status: 1, data: data })
    } else { 
      res.status(200).send({ status: 0 })
    }
  });
}

exports.create = (req, res) => {
  if (!req.body) {
    res.status(400).send({status:0, message: "Content can not be empty!" });
  }

  var time = new Date().toISOString().slice(0, 19).replace('T', ' ');
  var message = new Message({
    userId: req.body.userId != null ? req.body.userId : req.session.user.id,
    chatId: req.body.chatId,
    message: req.body.message,
    time_created: time
  });

  Message.create(message, (err, data) => {
    res.status(200).send({ status: 1 })
  });
}
