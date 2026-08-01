# Terms and Conditions

By using this extension you agree to the terms and conditions.
'''

with open("/mnt/agents/output/nfcgiftcards/config.json", "w") as f:
    f.write(config_json)
with open("/mnt/agents/output/nfcgiftcards/manifest.json", "w") as f:
    f.write(manifest_json)
with open("/mnt/agents/output/nfcgiftcards/description.md", "w") as f:
    f.write(description_md)
with open("/mnt/agents/output/nfcgiftcards/toc.md", "w") as f:
    f.write(toc_md)

print("Config, manifest, description, toc written")
