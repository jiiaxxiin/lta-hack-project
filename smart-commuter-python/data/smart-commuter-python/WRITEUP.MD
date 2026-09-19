# Smart Commuter Companion — Write-up

## 1. Persona and problem

Our application is designed for **Rachel**, a regular commuter travelling from Tampines to Raffles Place for work.

Rachel has taken the same route for several years and needs to arrive at work by **08:45**. On a normal day, her commute is predictable: she walks to Tampines MRT, takes the East West Line (EWL) to Raffles Place, then walks to her office.

The problem is that information about disruptions, crowding, weather and station facilities may come from different sources. Even when Rachel knows that a disruption exists, she still has to answer a more useful question:

> **Do I actually need to change what I am doing today?**

Our application is therefore designed as a commuter decision-support tool rather than simply another transport-information dashboard.

---

## 2. What the application does

The application first calculates Rachel's normal journey and treats it as her **baseline**.

It then considers available information about the current journey, including:

- train service disruptions;
- crowd density, where available;
- weather conditions;
- Rachel's personal journey constraints.

Instead of showing every possible transport option, the application gives Rachel a direct recommendation.

For example, on an ordinary day the application can tell her that there is nothing she needs to act on.

If there is only a small delay, it can keep her on her familiar route when changing route would not provide a meaningful benefit.

If her normal rail route becomes unavailable, the application can search the modelled transport network for an alternative journey.

---

## 3. Rachel's normal journey

Rachel's baseline commute is:

1. Walk from home near Tampines St 11 to Tampines MRT.
2. Take the East West Line from Tampines towards Raffles Place.
3. Walk from Raffles Place MRT to her office.

The application stores this baseline so that a disrupted journey can be compared against what Rachel normally expects.

The interface presents this as a stop-by-stop journey together with estimated journey time and a map.

---

## 4. Handling disruptions

A key design goal was to distinguish between a disruption that is merely informative and one that actually requires Rachel to change her journey.

### Minor delay

The supplied minor-delay replay demonstrates a case where the EWL is affected but the impact is not large enough to justify changing Rachel's route.

Instead of automatically rerouting whenever an alert exists, the application compares the disrupted journey against the baseline and can recommend staying with the normal journey.

This is reflected in the interface with a message such as:

> **Minor delay — not enough to change anything.**

### Major EWL disruption

The supplied signalling-fault replay represents a more severe case in which the affected EWL section cannot be used.

The affected stations are excluded from the usable network. The route planner then searches the remaining graph for another journey.

For Rachel's modelled network, this produces an alternative using the **Downtown Line from Tampines towards Chinatown**, followed by a walking leg towards her Raffles Place office.

The map simultaneously displays the unavailable EWL section, allowing Rachel to see both **what has failed** and **what she can do instead**.

The disruption scenario is injected/replayed test data and is explicitly labelled as simulated in the interface. It is not presented as a live disruption.

---

## 5. Routing approach

The transport network is represented as a graph.

MRT stations are nodes, while rail journeys and transfers are represented as edges. Each edge contains information such as its transport mode and estimated travel time.

The route planner searches this graph to find a usable journey between stations accessible from Rachel's origin and destination.

When a disruption occurs, affected stations can be blocked from the route search. This allows the same routing process to find an alternative using the remaining network rather than relying only on a manually written disruption message.

For the severe EWL scenario, blocking the affected EWL section allows the modelled Downtown Line connection at Tampines to become an alternative.

---

## 6. Decision logic

Finding a route is only one part of the application.

The application also compares the available journey with Rachel's normal journey and considers whether the change is significant enough to require action.

The advice layer considers information including:

- estimated journey-time difference from the baseline;
- available slack before Rachel's required arrival time;
- whether the normal route has become unusable;
- crowd information where available;
- weather near the journey origin;
- persona preferences.

This separates **route calculation** from **commuter advice**.

The intention is that Rachel should not have to interpret raw transport feeds herself. The application converts them into an actionable message such as leaving earlier, taking an alternative route, or making no change.

---

## 7. Architecture

The application uses a lightweight client-server architecture.

### Backend

The backend is implemented in **Python using FastAPI**.

Its responsibilities include:

- storing commuter personas;
- representing the transport network;
- calculating baseline and alternative journeys;
- applying disruptions to the network;
- estimating journey times;
- retrieving external data;
- generating commuter advice;
- loading replay scenarios; and
- supplying route geometry to the frontend.

The backend exposes API endpoints which are consumed by the browser interface.

### Frontend

The frontend is implemented with HTML, CSS and JavaScript.

It is responsible for presenting:

- the main recommendation;
- departure and arrival information;
- the stop-by-stop journey;
- normal-versus-current journey comparison;
- the interactive route map;
- reasons behind the recommendation;
- degraded-data warnings; and
- replay controls.

**Leaflet** is used to display the interactive map.

---

## 8. Geographic data and route visualisation

An early version of the prototype connected station coordinates using straight lines. Although sufficient for demonstrating routing logic, this did not accurately represent the physical railway alignment.

We therefore improved the map using detailed railway geometry derived from **OpenStreetMap**.

The repository contains locally stored geometry for:

- the East West Line; and
- the Downtown Line used by the alternative journey.

This allows the displayed railway routes to follow the mapped rail alignment rather than simply drawing a straight line between station coordinates.

For Rachel's demonstrated journey, walking access and egress geometry is also stored locally from captured pedestrian routes. This includes the demonstrated walking connections around Tampines, Raffles Place and Chinatown.

Storing these geometries locally makes the demonstration reproducible and prevents the core replay scenarios from depending on an external routing service being available during judging.

These captured walking routes are specific to the demonstrated journey and should not be interpreted as a general-purpose live pedestrian-routing system for arbitrary origins and destinations.

---

## 9. External data and graceful degradation

The application is designed to work with external transport and environmental information, including LTA DataMall and weather data.

However, an external API may be unavailable, return no relevant information, or require credentials that are not configured on the judging machine.

We therefore designed the application to **degrade explicitly rather than silently**.

If a source cannot be obtained, the application records this and displays a warning such as:

> Running on partial data: Crowd density for EWL unavailable.

The application can continue using the information that remains available rather than interpreting missing data as evidence that conditions are normal.

This also makes failures visible to the user and to a judge inspecting the application.

---

## 10. Replay and reproducibility

Transport disruptions are unpredictable. A real EWL disruption may not occur while the application is being judged.

For this reason, the repository contains replay/injected scenarios that reproduce important application behaviour.

The demonstrated scenarios include:

- an East West Line minor delay; and
- an East West Line signalling fault with a more severe service impact.

Replay data is explicitly labelled as simulated in the user interface.

This allows a judge to reproduce the application's decision-making behaviour without waiting for a real disruption.

---

## 11. User-interface design

The interface is designed around the question:

> **What does Rachel need to do?**

The recommendation is therefore presented before the detailed transport information.

Supporting information is progressively available below it:

1. the recommended action;
2. the journey stop by stop;
3. comparison with Rachel's usual journey;
4. the geographic route;
5. reasons for the change; and
6. the underlying transport alert where available.

This structure attempts to reduce the amount of information Rachel needs to interpret while still making the application's reasoning inspectable.

The visual design also distinguishes route states on the map. For example, the disrupted EWL section is shown separately from the alternative route so that the cause and response can be understood together.

---

## 12. Assumptions and limitations

The prototype is deliberately focused on Rachel's Tampines-to-Raffles Place commute.

It is not a complete model of Singapore's public-transport network.

The main limitations are:

- only the transport network needed for the demonstrated journey and alternative is modelled in detail;
- some station coordinates are approximate station centroids rather than individual entrances;
- detailed walking geometries are captured for the demonstrated journey rather than dynamically calculated for arbitrary locations;
- locally stored rail geometry is used to make the demonstration reproducible;
- travel times are planning estimates rather than guaranteed arrival times;
- crowd, other live information depends on the availability of upstream data sources; and
- replayed disruption scenarios demonstrate system behaviour but are not claims about current network conditions.

These limitations are intentionally exposed rather than hidden so that the scope of the prototype remains clear.

---

## 13. What we would improve next

With additional development time, we would extend the transport graph to cover more MRT lines and stations and replace journey-specific walking geometry with live pedestrian routing.

We would also improve station entrance and interchange modelling so that walking, transfer and rail geometries connect at precise pedestrian-access points.

This would allow the same decision-support approach to be applied to additional commuters and arbitrary origin-destination pairs while retaining the current baseline-versus-disruption comparison.

---

## 14. Summary

Smart Commuter Companion is designed to move beyond simply telling a commuter that a disruption exists.

For Rachel, the application maintains an understanding of her normal commute, evaluates changing conditions, and attempts to answer the more useful question:

> **Does this change what I should do today?**

A minor disruption can therefore result in no change, while an unusable normal route can trigger an alternative journey.

The combination of persona-specific decision logic, route planning, explicit degraded-data handling, reproducible disruption replay and geographic route visualisation forms the core of the prototype.
