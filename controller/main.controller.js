const Chat = require("../models/chats.js");
var chat = require("../models/chats.js");

exports.showIndex = (req, res) => {
    var chatRooms = [];
    if(req.session.user) {
        chat.getAll((err, data) => {
            chatRooms = data;

            res.render('index', { 
                session: req.session,
                chats: chatRooms
            });
        });
    } else {
        res.render('index', { 
            session: req.session,
            chats: chatRooms
        });
    }
};