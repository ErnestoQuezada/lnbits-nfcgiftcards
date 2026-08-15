<img src="https://raw.githubusercontent.com/ErnestoQuezada/lnbits-nfcgiftcards/main/static/image/paid.png" alt="Invoice paid" width="400" height="267">

# NFC Gift Cards for LNbits

NFC Gift Cards brings physical Lightning payments into the real world by allowing LNbits users to create rechargeable gift cards stored on NFC tags.

The extension allows you to write Lightning-powered gift cards onto compatible NFC tags such as NTAG215 and similar NFC devices. Each card can hold a balance that can be redeemed by scanning the NFC tag with a compatible device.

## Features

* Create Lightning gift cards using LNbits
* Store gift card information on NFC tags
* Recharge existing gift cards
* Redeem gift card balances through a simple NFC interaction
* Support for affordable, reusable NFC hardware
* Integrates directly with your LNbits wallet infrastructure


## How it works

1. Create a gift card from your LNbits wallet.
2. Write the gift card information to an NFC tag.
3. Give the physical NFC card to another person.
4. The recipient can scan the tag and redeem the available Lightning balance.

<img src="https://raw.githubusercontent.com/ErnestoQuezada/lnbits-nfcgiftcards/main/static/image/nfc-gift-cards.png" alt="Invoice paid" width="400" height="267">

## Use cases

NFC Gift Cards can be used for:

* Physical Lightning gifts
* Bitcoin onboarding experiences
* Store credit systems
* Event vouchers
* Community rewards
* Point-of-sale experiments
* Educational Bitcoin demonstrations

## NFC Hardware

The extension is designed to work with common NFC tags, including NTAG215 and compatible devices. Different NFC hardware may have different storage capacities and capabilities.

## Security considerations

NFC tags are physical objects and should be treated accordingly. Users should consider their threat model when deploying gift cards, especially for high-value balances.

For larger amounts, additional safeguards such as redemption limits, verification steps, or secure distribution methods may be appropriate.

## Requirements

* LNbits 1.5.0 or later
* A Lightning wallet configured with LNbits
* Compatible NFC tags
* An NFC-capable phone or reader

## License

This project is released under the MIT License.
