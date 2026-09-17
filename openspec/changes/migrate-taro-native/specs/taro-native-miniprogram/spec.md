# Taro Native Mini-Program Specification

## Overview

This specification defines the requirements for migrating the H5 React app to a Taro-based native WeChat mini-program, bypassing the web-view limitation for personal accounts.

---

## ADDED Requirements

### Requirement: Taro Framework Build

The system MUST use Taro 3.x framework with React to generate native WeChat mini-program code. No web-view dependencies SHALL be present.

#### Scenario: Development Build

- **GIVEN**: Developer runs `npm run dev:weapp`
- **WHEN**: Taro compilation completes
- **THEN**: A `dist/` directory is generated containing native mini-program code
- **AND**: WeChat Developer Tools can load and preview the project

#### Scenario: Production Build

- **GIVEN**: Developer runs `npm run build:weapp`
- **WHEN**: Build completes
- **THEN**: Optimized mini-program code is generated for release

---

### Requirement: Remote JSON Data API

The system MUST fetch data from the existing server JSON API using `Taro.request`. No backend changes SHALL be required.

#### Scenario: Load Character Data

- **GIVEN**: Server provides `https://shushu.host/jianlai/data/characters_top.json`
- **WHEN**: Home page loads and calls `useTopCharacters()`
- **THEN**: 20 character objects are returned for rendering

#### Scenario: Network Error Handling

- **GIVEN**: Network is unavailable or server is down
- **WHEN**: Request fails
- **THEN**: A user-friendly error message is displayed
- **AND**: App does not crash

---

### Requirement: Core Page Implementation

The mini-program MUST include all core pages with functionality consistent with the H5 version.

#### Scenario: Home Page Display

- **GIVEN**: User opens the mini-program
- **WHEN**: Home page finishes loading
- **THEN**: Character horizontal scroll list is displayed
- **AND**: Category entries (factions, artifacts, locations) are shown
- **AND**: Daily quote section is visible

#### Scenario: Character List and Detail

- **GIVEN**: User taps character entry
- **WHEN**: Character list loads
- **THEN**: Character grid is displayed with avatars and names
- **AND**: Tapping a character navigates to detail page

#### Scenario: Compendium Lists

- **GIVEN**: User taps factions/artifacts/locations entry
- **WHEN**: List page loads
- **THEN**: Corresponding compendium data is displayed
- **AND**: Tapping an item navigates to detail page
