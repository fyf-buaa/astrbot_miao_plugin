# AstrBot Miao Plugin

A multi-functional query plugin for Genshin Impact and Honkai: Star Rail

## Introduction

AstrBot Miao Plugin is a game query plugin developed for the [AstrBot](https://github.com/AstronIsm/astrbot) framework, supporting character data queries, profile management, WIKI lookup, and more for miHoYo games. Currently supports Genshin Impact and Honkai: Star Rail.

## Features

| Feature | Description |
|---------|-------------|
| **Profile Query** | View detailed character cultivation data |
| **Character Cards** | Generate beautiful character display images |
| **WIKI Query** | Retrieve information on character skills, talents, materials, etc. |
| **Damage Calculation** | Calculate character damage output potential |
| **Leaderboard** | Character data ranking within group chats |
| **Calendar** | In-game event and character birthday calendar |
| **Material Tracking** | Daily dungeon and ascension material reminders |

## Supported Games

- `gs` - Genshin Impact
- `sr` - Honkai: Star Rail

## Installation Dependencies

```bash
pip install -r requirements.txt
```

## Configuration Guide

Plugin configuration options are defined in `_conf_schema.json`. Main configurations include:

- API service settings (Enka API / Mihomo API)
- Rendering style settings
- Administrator settings
- Feature toggles

Basic configuration must be performed via bot administrator commands upon first use.

## Usage

### Basic Commands

```
/help                - Get help information
/版本                - Check plugin version
面板帮助             - View profile-related commands
喵喵角色卡片