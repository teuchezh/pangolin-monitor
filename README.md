# Pangolin Monitor Integration for Home Assistant

This integration connects Home Assistant with Pangolin  

![example](images/lovelace-card.png)

Previously I used Cloudflare Zero Trust Tunnel and after switching to Pangolin I realized that I lacked monitoring, and so I decided to quickly make an addon for monitoring the status of my tunnels.  
I will be glad to receive suggestions for new functionality.  
## Features

- Authenticate using email and password
- Tracks tunnels/sites registered in Pangolin
- Displays state (online/offline) and stats per tunnel

## Configuration

1. Go to Home Assistant Integrations
2. Add new integration -> Pangolin Monitor
3. Provide your Pangolin email, password, and server base URL

## Jinja Generator script for mushroom template cards

🔧 How to use:

Go to Home Assistant → Developer Tools → Templates.

Paste the Jinja code above and copy the generated YAML.

Paste it into Lovelace as a "Manual Card" (or into a vertical-stack if there are multiple cards).

```jinja
{% for entity in states.sensor 
     if entity.entity_id.startswith('sensor.pangolin_tunnel_') %}
- type: custom:mushroom-template-card
  primary: Tunnel {{ entity.attributes.name or entity.entity_id.split('_')[-1] }}
  secondary: >
    Status: {{ '{{ states("' ~ entity.entity_id ~ '") }}' }}
    In: {{ '{{ (state_attr("' ~ entity.entity_id ~ '", "megabytes_in") / 1024) | round(2) }} GB ·
    Out: {{ (state_attr("' ~ entity.entity_id ~ '", "megabytes_out") / 1024) | round(2) }} GB' }}
  icon: mdi:cloud-outline
  icon_color: orange
  entity: {{ entity.entity_id }}
  layout: horizontal
  tap_action:
    action: more-info
{% endfor %}
```

## Disclaimer
This project is not affiliated with or endorsed by Pangolin.