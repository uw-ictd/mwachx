Mwach Codebase Documentation
----

The aim of this document is to provide an overview orientation of the mwachx codebase.
Make sure to read the [caveat](#caveat)

In addition to this writeup, see [this google doc](https://docs.google.com/document/d/1vL0r3hVkuJeNQTZUWSBpMCdsLXgw_UKaXNfKHANSOeE/edit#)
for some high-level information about the future direction of the platform and desired architectural changes.

# Apps

The following are the key apps in the codebase:

* The `backend` app contains the models and logic for automated messages in the system.
* The `contacts` app contains the main data models and logic for the (SMS) contacts in the system.
* The `transports` app has the logic around gateways and SMS routing and validation
* The `utils` app contains shared utility code as well as management commands that handle the scheduled tasks for the system
  (including automated messages)

# Models

## mwachx.backend

The `backend` app contains the models and logic for automated messages in the system.

The messages are stored as instances of the `AutomatedMessage` model.
Each `AutomatedMessage` has fields that contain information about when it should be sent (e.g. `send_base`, `group`, `condition`, etc.
These fields are combined to form a `description` which is a (hopefully) unique text identifier combining the relevant fields
of the message into a single identifier.
This `description` is mapped to `Contact.description` and can be queried with logic in the `AutomatedMessageQuerySet` class.

### Possible (Unvetted) Todos

* The logic for getting a message from a contact / description is quite hard-coded and specific.
  Maybe figure out a plug-in style architecture? Or maybe introduce project-specific subclasses.

## mwachx.contact

This module contains the main data models and logic for the contacts in the system.

The `Contact` model represents each person/participant in the system, and contains a slew of fields for representing their
demographic and medical information and status. `StatusChange` tracks any status changes that happen to Contacts.

The `Message` and `PhoneCall` models (in `contacts.models.interactions`) represent individual instances of messages/calls.

The `Note` model is a very simple freetext note linked to a person.

The `EventLog` model logs web-based events (which are not used for anything currently)

### Possible (Unvetted) Todos

* Split out `Contact` into a generic base class and add project-specific implementations that live outside the core models.
  Some work was done in this space built on [django swappable models](https://github.com/wq/django-swappable-models).
* Introduce a `Participant` model to separate the notion of contact from someone actually participating in a study
* Lots of hard-coded scheduling logic living as methods on `Contact`. Could pull these out into an isolated place?
* Generally reduce the footprint of the `Contact` model and pull helper code into helper / logical units
* Rename `SchedualQuerySet` to remove typo
* Could the `EventLog` model be removed if it is not used?

# Front End

The front end uses angular.js, restangular, Django REST Framework, and [UI Bootstrap](https://angular-ui.github.io/bootstrap/).
Most of the relevant code is in `mach/static/app/`.

Each "route" contains a url, a template and a controller.
The controller grabs some data (typically using Restangular), sets it in a `$scope` variable, and then renders it using the template.

## mawchx.routes.js

This is where the routes are defined. These largely correspond to pages/tabs in the app.
Each route points to a template that is a *subset* of the overall template (which lives in `contacts/templates/app/index.html`),
as well as a controller that is defined in a javascript file.

## mawchx.module.js

This is the main entry point to the front-end code and is where Restangular is configured.

## mwachxAPI

The `mwachxAPI` class provides an interface to data in the system (see `/mwach/static/app/shared/mwDataService.js`).
These correspond to Django REST Framework endpoints.

Each endpoint is prepended with a URL (`/api/v0.1/`) that is configured in `mawchx.module.js`.
So for example the following code:

```javascript
service.visits = Restangular.all('visits');
```

Connects `mwachxAPI.visits` to be backed by the data from http://localhost:8000/api/v0.1/visits.

### Possible (Unvetted) Todos

* Should the references to non-existent `service.facilities` API be removed to prevent confusion from future developers?

# Messaging

Most of the messaging logic lives in `mwachx.transports`.

Each transport is defined as a module in `mwachx.transports` that implements a `send` function for outbound messages.

Additionally, each transport can (optionally) define a set of views that serve as hooks for inbound messages.
These views should call `transports.receive()` with the appropriate message information.
This function serves as the entry point for all inbound messaging.

## Message Schedules

Currently the majority of the logic for message schedules is handled by the `send_messages` management
command in the `mwachx.utils` app. The logic goes approximately like this:

1. For each eligible message type (e.g. weekly, missed visits, etc.):
1. Determine the list of participants available for messages (handled by functions in the `send_messages` module)
1. Send a message to those participants according to their current state (handled either by the functions in
   the `send_messages` module, or by the `Contact.send_automated_message` function.

# Deployment

During the initial stages this project used Openshift , but it now now uses Webfaction.
All references in the code to openshift can be removed.

Deployment goes like this:

- `git push webfaction`
- `ssh webfaction`
- `./mwachx/bin/deploy`

The deploy script runs the [webfaction gulp commands](https://github.com/tperrier/mwachx/blob/master/gulpfile.js).
I'm sure there's a better way to do this and I wish I had something more like local_settings.py for gulp.
I haven't really put much effort into optimizing this since the current method works though is a massive hack.

# Settings

Originally the `MESSAGING_CONNECTION`, and `MESSAGING_ADMIN` settings were created
to make it possible to easily swap out different models for these things, however it is not
expected that these will work as-advertised.

For the `Contact` mode, the `swapper` utilities should be used.

# Overall (Unvetted) Todos

* Add more unit tests.
* Upgrade to latest django + dependencies.
* Standardize deployment with `fabric`
* Documentation
  * Explain how SMS templates work, how new SMS messages get into the system
  * Explain purpose of `FAKE_DATE` and when to use it (looks like just for dev/debug purposes and yet it defaults to `True` if not present).
* Architecture/Code
  * Consider getting rid of "description" passthroughs - convert to a class that knows how to serialize itself if necessary
  * Consider removing `MESSAGING_CONTACT` (and similar) settings, or make it so that they are actually properly supported (partially done).
  * Consider making a concrete link between `Message` and `AutomatedMessage` in the case of automated messages being sent?
* App / bugs
  * (very minor) header covers mother name a bit on certain screen sizes

# Caveat

This document was written by [Cory Zue](https://github.com/czue) during a project/architecture review.
Cory was *not* an active developer/maintainer of the codebase and so may have gotten some things wrong
in these docs.
