# Udacity Catalog
This is a web application that provides a list of items within a variety of categories and integrate third party user registration and authentication. Authenticated users should have the ability to post, edit, and delete their own items.

# Something you may need
Vagrant: https://www.vagrantup.com/
Udacity Vagrantfile: https://github.com/udacity/fullstack-nanodegree-vm
VirtualBox https://www.virtualbox.org/wiki/Downloads

# Getting Started
1.Install Vagrant and VirtualBox if you have not done so already. Instructions on how to do so can be found on the websites as well as in the course materials..https://www.udacity.com/wiki/ud088/vagrant.
2.Launch the Vagrant VM (by typing vagrant up in the directory fullstack/vagrant from the terminal). You can find further instructions on how to do so here.
https://www.udacity.com/wiki/ud088/vagrant.
3.go to /vagrant/catalog, log in to db using command: sqlite3 catalog.db
4.run the db_init.sql script using this command: .read db_init.sql
5.quit sqlite3 using control+d
6.run the application using command: python application.py
7.go to "http://localhost:5000/" to check the website.

##JSON Endpoints
`/categories/<int:category_id>/item/<int:catalog_item_id>/JSON` -- JSON of specific item in catalog

`/categories/<int:category_id>/items/JSON` -- JSON of all items of a given category

`/catalog.json` -- JSON of all items

`/categories.json` -- JSON of all categories
