#!/bin/bash
# Add missing Cloudflare IP ranges to UFW

# Cloudflare IPv4 ranges
CF_IPS=(
    "197.234.240.0/22"
    "198.41.128.0/17"
    "162.158.0.0/15"
    "104.16.0.0/13"
    "104.24.0.0/14"
    "172.64.0.0/13"
    "131.0.72.0/22"
)

echo "Adding missing Cloudflare IP ranges to UFW..."

for ip in "${CF_IPS[@]}"; do
    echo "Adding $ip..."
    ufw allow from $ip to any port 80 proto tcp comment 'Cloudflare'
    ufw allow from $ip to any port 443 proto tcp comment 'Cloudflare'
done

echo "✅ All Cloudflare IP ranges added"
echo ""
echo "Reloading UFW..."
ufw reload
echo "✅ UFW reloaded"
