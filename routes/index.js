var express = require('express');
var router = express.Router();
var users = require("../controller/user.controller.js");
var controller = require("../controller/main.controller");

router.get('/', controller.showIndex);

router.get('/registration', function(req, res) {
  if(req.session.user) {
    res.redirect('/')
  } else {
    res.render('registration');
  }
});

router.get('/logout', function(req, res) {
  req.session.destroy();
  res.status(200).send({ message: "logged out" });
});

router.post('/login', users.login);

module.exports = router;
