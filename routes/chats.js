var express = require('express');
var router = express.Router();
var chats = require("../controller/chat.controller.js");
var messages = require("../controller/message.controller.js");

router.get("/:id", chats.getChatById);

router.get("/room/:id", chats.show);

router.post("/", chats.create);

router.post("/messages", messages.create);

router.get("/:chatId/messages/:time", messages.getByChat)

module.exports = router;