# Tech Stack
There are a few parameters I considered when deciding upon the tech stack I was going to use for the app:
1. Educational Potential - My knowledge of web development is very minimal. I would like to use this opportunity to gain some more useful tools and knowledge in the field.
2. Usefulness - Ideally the tools I use should be ones that are rather widely used in the industry.
3. Simplicity - This is a rather simple app and I wouldn't want to find myself flying through hoops just to get it above ground.

The chosen stack is **Django + Django REST Framework** on the backend and **React (via Vite)** on the frontend. Django provides a mature ORM, built-in admin, and a straightforward path to a REST API through DRF. React handles the interactive UI — particularly the live countdown timer, which runs client-side and only syncs with the server on pause or stop (storing `time_remaining` and `started_at` on the server rather than ticking every second). Authentication is handled via JWT tokens using `djangorestframework-simplejwt`. SQLite is used during development with a clean upgrade path to PostgreSQL for production.


# API

The basic version of the app will have the following API functions:

| URL                | Description                                      | Parameters                                       | Return Value                                                                                              | Method |
| ------------------ | ------------------------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | ------ |
| /api/habits        | Get data about all habits of the requesting user | None                                             | JSON containing list of all habits. For each habit: id, name, description, period, time                   | GET    |
| /api/habits/\<id\> | Get data about specific habit                    | Habit ID                                         | Json containing the following data for the requested habit (only if it belongs to the authenticated user) | GET    |
| /api/habits/create | Create a new habit                               | New habbit's name, description, period and time. | New habit ID or error                                                                                     | POST   |
| /api/habits/\<id\> | Edit existing habit                              | New field values (a "dict update" is performed)  | Error code                                                                                                | PATCH  |
| /api/timing        | Get current times for all habits of user         |                                                  | Map of habit id to remaining time.                                                                        | GET    |
| /api/timing/\<id\> | Get current time of specific habit               |                                                  | remaining time of habit                                                                                   | GET    |
| /api/timing/\<id\> | Set new current time for habit                   | New current time for habit                       |                                                                                                           | PUT    |
|                    |                                                  |                                                  |                                                                                                           |        |

## Adding a Habit

A habit is an object that contains the following values:

| Parameter Name    | Parameter Type | Description                                                       |
| ----------------- | -------------- | ----------------------------------------------------------------- |
| Habit ID          | Number         | Identifies this specific habit                                    |
| User ID           | Number         | User to which this habit is assigned                              |
| Habit Name        | String         | The name used to identify the habit by the user                   |
| Habit Description | String         | Optional description of the habit that could be added by the user |
| Habit Period      | Enum           | This will be either daily or weekly.                              |
| Habit time        | Number         | Time, in minutes, that this habit is given within the period.     |


# UI

The basic version of the app will consist of three screens:

* Main Screen - This is where you will see all of your habits along with the amount of time left for each of them. Habits that are completed will be painted green, habits that are not will be painted red. Clicking a habit would transition to the "Habit timing" screen for that habit. There will be a sliding menu to the left (which will open by clicking a button on the top left) with the following tabs: "Main" (current screen), "Manage Habits" (moves to the "habit management screen") and "About" (moves to a screen with info about the app).
* Habit timing screen - in the center of this screen will be a timer with the time left for this habit. below the timer will be a large round play button, which will change into a pause button once clicked. Pressing the timer itself would allow a value to be entered into it manually. In the top left will be a "go back" button that will lead back to the main screen.
* Habit management screen - in this screen, all habits for the current user will apper in a list, separated by daily and weekly habits. Clicking a habit would allow editing it's parameters (name, description, period and time). There will also be a button to delete the habit. On the bottom right will be a floating "+" button that would lead to a form for creating a new habit.
