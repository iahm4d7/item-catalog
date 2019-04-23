

# Project: Item Catalog
**Ahmed al-hameed**


 ## Project  overview:

The Item Catalog project consists of developing an application that provides a list of items within a variety of categories, as well as provide a user registration and authentication system.


only a user can add new items, edit or delete only their created items. Anyone can view items in the catalog


## Project content

in zip file you will find:

- **item_catalog.py**: the flask app you will be running.
- **templates**: a folder with all the HTML
- **static**: a folder that contains the CSS
- **database_setup.py**: the setup for the database
- **fill_database.py**: a script to add objects to the database
- **itemcatalog.db**: the database itself (you don't need to run database_setup.py)
- **client_secrets.json**: a json object the contains all the necessary keys for oauth
- **README.md**: this file!


## Requirements

-   [VirtualBox](https://www.virtualbox.org/)
-   [Vagrant](https://www.vagrantup.com/)
-   [Python 2.7](https://www.python.org/)](https://www.python.org/)
-   [Bash terminal(for windows machine)](https://git-scm.com/downloads)

## Installation

1.  Install Python2.7 , VirtualBox and Vagrant

2.  Clone or download the Vagrant VM configuration file from  [fullstack-nanodegree-vm repository](https://github.com/udacity/fullstack-nanodegree-vm)

3.  download this zip file to your desktop , Unzip and  Paste all the files  from this project  `Item-Catalog` into the ```fullstack-nanodegree-vm-master\vagrant\catalog ``` sub-directory



## Steps to run this project

1.  Open terminal and go to the folder where you saved the fullstack repository then run the following:
 `cd vagrant`.
2.  Launch Vagrant to set up the virtual machine and then log into the virtual machine with
  `vagrant up`  `vagrant ssh`

3. Then move inside the catalog folder:
`cd /vagrant/catalog`

4. Then run the application:
`python item_catalog.py`

5. finally Access and test your application by visiting  [http://localhost:5000](http://localhost:5000/)




## Output
###### by visiting [http://localhost:5000](http://localhost:5000/) or [http://localhost:5000/catalog](http://localhost:5000/catalog) it will take you to the site's main page.

  a user that is not logged in will only be able to view categories and books, if you log in using Google account you will then be able to add, edit, and delete items.
