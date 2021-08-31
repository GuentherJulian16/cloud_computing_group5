const User = require("../models/users.js");

// Retrieve all users from the database.
exports.findAll = (req, res) => {
  User.getAll((err, data) => {
    if (err)
      res.status(500).send({
        message:
          err.message || "Some error occurred while retrieving users."
      });
    else res.send(data);
  });
};

exports.create = (req, res) => {
  if (!req.body) {
    res.status(400).send({status:0, message: "Content can not be empty!" });
  }

  // Check if password equals the repeated password
  if(req.body.password != req.body.passwordConfirm) {
    res.status(200).send({ status:0, kind: "passwords_dont_match" });
  } else {

    const user = new User({
      username: req.body.username,
      password: req.body.password
    });

    // Check if user already exists <-- User.search should not work, need to implement email check
    User.getUserByName(user, (err, data) => {
      if(!data) {
        //Save User in the database
        User.create(user, (err, data) => {
          if (err) {
            res.status(500).send({ status:0, message: err.message || "Some error occurred while creating the User." });
          } else {
            // If registration was successful, set session parameters and navigate to home
            req.session.user = data;
            res.status(200).send({ status: 1 })
          }
        });
      } else {
        res.status(200).send({ status:0, kind: "user_already_exists" });
      }
    });
  }
};

exports.login = (req, res) => {
  if (!req.body) {
    res.status(400).send({ message: "Content can not be empty!" });
  }

  const user = new User({
    username: req.body.username,
    password: req.body.password,
  });

  User.getUserByNameAndPassword(user, (err, data) => {
    if(data) {
      req.session.user = data[0];
      res.status(200).send({ status: 1 })
    } else {
      res.status(200).send({ status: 0 })
    }
  });
};