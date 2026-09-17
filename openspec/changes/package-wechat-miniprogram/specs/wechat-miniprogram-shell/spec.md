# 微信小程序壳规范

## 概述

本规范定义微信小程序壳的功能需求，用于封装《剑来·万象图录》H5 应用。

---

## ADDED Requirements

### Requirement: Web-View H5 Loading

The system MUST load and display the H5 application using the `web-view` component. Users SHALL be able to browse and use all H5 functionality normally.

#### Scenario: User opens miniprogram

- **GIVEN**: User has WeChat installed and found the miniprogram
- **WHEN**: User taps to enter the miniprogram
- **THEN**: The miniprogram displays H5 homepage content
- **AND**: User can browse character list, artifact list, and other pages normally
- **AND**: Page interactions (click, scroll, search) work correctly

#### Scenario: H5 page loading fails

- **GIVEN**: Network error or H5 service unavailable
- **WHEN**: web-view times out or encounters an error
- **THEN**: A friendly error message is displayed
- **AND**: A retry button is provided

---

### Requirement: Share Forwarding

The system MUST support forwarding and sharing functionality. Users SHALL be able to share the miniprogram to WeChat friends or group chats.

#### Scenario: User shares miniprogram

- **GIVEN**: User is using the miniprogram
- **WHEN**: User taps "Forward" in the top-right menu
- **THEN**: A share card is displayed with custom title and image
- **AND**: Share title is "剑来·万象图录 - 你的江湖知识库"
- **AND**: Friends can open the miniprogram by tapping the share card

---

### Requirement: WeChat Configuration Compliance

The miniprogram configuration MUST comply with WeChat specifications. Configuration files SHALL contain all necessary information to meet WeChat miniprogram review requirements.

#### Scenario: Configuration validation

- **GIVEN**: Miniprogram project has been created
- **WHEN**: Opening the project with WeChat Developer Tools
- **THEN**: Developer Tools shows no configuration errors
- **AND**: `app.json` contains correct page routes
- **AND**: `project.config.json` contains a valid AppID

---

### Requirement: Miniprogram Environment Detection

The H5 application MUST correctly detect the miniprogram environment. The application SHALL be able to identify whether it is running inside the miniprogram's web-view for environment adaptation.

#### Scenario: Detect miniprogram environment

- **GIVEN**: H5 application has included WeChat JS-SDK
- **WHEN**: H5 application starts and checks runtime environment
- **THEN**: It correctly identifies whether running in miniprogram web-view
- **AND**: UI or functionality can be adjusted based on environment (e.g., hide inapplicable features)
