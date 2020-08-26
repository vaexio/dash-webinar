# dash-webinar
A Dash app powerd by Vaex - Plotly webinar August 2020

See also the more full fledged example https://github.com/vaexio/dash-120million-taxi-app which is live at https://dash.vaex.io

# Try out this project in Dash Enterprise workspace

 * Create a new app in Dash Enterprise
 * Create a workspace
 * Open the workspace
 * Open the terminal in the workspace
 * Execute the following:
 ```
git remote add github https://github.com/vaexio/dash-webinar.git
git fetch github
git reset --hard github/master
pip install --upgrade pip
pip install -r requirements.txt
```

 * Run the app.ipynb notebook, it should look like this:
 <img width="1279" alt="Screen Shot 2020-08-26 at 15 08 01" src="https://user-images.githubusercontent.com/1765949/91307903-da3d5600-e7ae-11ea-8159-bf774b4ce005.png">


## Deploy
 * Run in the terminal
 ```
 git push plotly --force (the force is only needed the first time)
 ```
