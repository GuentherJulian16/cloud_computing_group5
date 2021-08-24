var express = require('express');
var router = express.Router();
var users = require("../controller/user.controller.js");

router.get('/', users.findAll);

router.post("/", users.create);

module.exports = router;
