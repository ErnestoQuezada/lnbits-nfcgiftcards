console.log('[NFC Gift Cards] SCRIPT LOADED')

try {
  window.app = Vue.createApp({
    el: '#vue',
    mixins: [windowMixin],
    data() {
      return {
        ready: false,
        creating: false,
        recharging: false,
        rechargeAmount: '',
        giftCards: [],
        selectedCard: null,
        written: false,
        form: {
          amount: '',
          note: '',
          expires_at: ''
        },
        nfcSupported: false,
        writingNfc: false,
        nfcMessage: '',
        nfcError: false,
        listLoading: false
      }
    },
    computed: {
      nfcBannerClass() {
        return this.nfcError ? 'bg-negative text-white' : 'bg-positive text-white'
      },
      showWithdraw() {
        return !this.written
      },
      rechargeQrUrl() {
        if (!this.selectedCard) return ''
        // Prefer backend-provided QR URL
        if (this.selectedCard.lnurlp_qr_url) {
          return this.selectedCard.lnurlp_qr_url
        }
        // Fallback: construct from bech32
        if (this.selectedCard.lnurlp_bech32) {
          var base = window.location.protocol + '//' + window.location.host + '/'
          return base + 'api/v1/qrcode/' + encodeURIComponent(this.selectedCard.lnurlp_bech32)
        }
        // Last resort: construct from raw URL
        if (this.selectedCard.lnurlp_url) {
          var base2 = window.location.protocol + '//' + window.location.host + '/'
          return base2 + 'api/v1/qrcode/' + encodeURIComponent(this.selectedCard.lnurlp_url)
        }
        return ''
      }
    },
    methods: {
      async fetchGiftCards() {
        try {
          var wallet = this.g.user.wallets[0]
          this.listLoading = true
          var response = await LNbits.api.request(
            'GET',
            '/nfcgiftcards/api/v1/nfcgiftcards',
            wallet.inkey
          )
          var raw = response && response.data
          console.log('[NFC Gift Cards] fetch raw:', raw)
          if (Array.isArray(raw)) {
            this.giftCards = raw.map(function(c) {
              var card = {
                id: c.id || '',
                note: c.note || '',
                amount: c.amount || 0,
                balance: c.balance || 0,
                lnurl: c.lnurl || '',
                qr_url: c.qr_url || '',
                lnurlp_url: c.lnurlp_url || '',
                lnurlp_bech32: c.lnurlp_bech32 || '',
                lnurlp_qr_url: c.lnurlp_qr_url || '',
                expires_at: c.expires_at || null,
                is_expired: false
              }
              console.log('[NFC Gift Cards] mapped card:', card.id, 'lnurlp_qr_url:', card.lnurlp_qr_url)
              return card
            })
            var now = new Date()
            this.giftCards.forEach(function(card) {
              if (card.expires_at) {
                card.is_expired = now > new Date(card.expires_at)
              }
            })
          } else {
            this.giftCards = []
          }
        } catch (err) {
          console.error('[NFC Gift Cards] fetch error:', err)
          this.giftCards = []
        } finally {
          this.listLoading = false
        }
      },
      async createGiftCard() {
        try {
          var wallet = this.g.user.wallets[0]
          var amt = parseInt(this.form.amount)
          if (isNaN(amt) || amt < 1) {
            this.$q.notify({type: 'negative', message: 'Amount must be at least 1 sat'})
            return
          }
          this.creating = true
          var payload = {amount: amt}
          if (this.form.note) payload.note = this.form.note
          if (this.form.expires_at) {
            payload.expires_at = new Date(this.form.expires_at).toISOString()
          }
          var response = await LNbits.api.request(
            'POST',
            '/nfcgiftcards/api/v1/nfcgiftcards',
            wallet.adminkey,
            payload
          )
          this.selectedCard = (response && response.data) ? response.data : null
          this.written = false
          this.form = {amount: '', note: '', expires_at: ''}
          await this.fetchGiftCards()
          this.$q.notify({type: 'positive', message: 'Gift card created!'})
        } catch (err) {
          console.error('[NFC Gift Cards] create error:', err)
          LNbits.utils.notifyApiError(err)
        } finally {
          this.creating = false
        }
      },
      async rechargeCard() {
        if (!this.selectedCard) return
        var amt = parseInt(this.rechargeAmount)
        if (isNaN(amt) || amt < 1) {
          this.$q.notify({type: 'negative', message: 'Recharge amount must be at least 1 sat'})
          return
        }
        this.recharging = true
        try {
          var wallet = this.g.user.wallets[0]
          var response = await LNbits.api.request(
            'PUT',
            '/nfcgiftcards/api/v1/nfcgiftcards/' + this.selectedCard.id + '/recharge',
            wallet.adminkey,
            {amount: amt}
          )
          this.rechargeAmount = ''
          await this.fetchGiftCards()
          var updated = this.giftCards.find(function(c) { return c.id === this.selectedCard.id }.bind(this))
          if (updated) this.selectedCard = updated
          this.$q.notify({type: 'positive', message: response.data.message || 'Recharged!'})
        } catch (err) {
          console.error('[NFC Gift Cards] recharge error:', err)
          LNbits.utils.notifyApiError(err)
        } finally {
          this.recharging = false
        }
      },
      async deleteCard(id) {
        try {
          var wallet = this.g.user.wallets[0]
          await LNbits.api.request(
            'DELETE',
            '/nfcgiftcards/api/v1/nfcgiftcards/' + id,
            wallet.adminkey
          )
          if (this.selectedCard && this.selectedCard.id === id) {
            this.selectedCard = null
          }
          await this.fetchGiftCards()
          this.$q.notify({type: 'positive', message: 'Gift card deleted.'})
        } catch (err) {
          LNbits.utils.notifyApiError(err)
        }
      },
      selectCard(card) {
        this.selectedCard = card
        this.written = false
        this.nfcMessage = ''
        this.nfcError = false
        this.rechargeAmount = ''
        console.log('[NFC Gift Cards] selected card:', card.id, 'lnurlp_qr_url:', card.lnurlp_qr_url, 'rechargeQrUrl:', this.rechargeQrUrl)
      },
      isCardActive(card) {
        return this.selectedCard && this.selectedCard.id === card.id
      },
      cardCaptionClass(card) {
        return this.isCardActive(card) ? 'text-white' : 'text-grey'
      },
      copyLnurl() {
        if (!this.selectedCard || !this.selectedCard.lnurl) return
        navigator.clipboard.writeText(this.selectedCard.lnurl).then(() => {
          this.$q.notify({type: 'positive', message: 'LNURL copied to clipboard'})
        })
      },
      copyLnurlPay() {
        if (!this.selectedCard || !this.selectedCard.lnurlp_bech32) return
        navigator.clipboard.writeText(this.selectedCard.lnurlp_bech32).then(() => {
          this.$q.notify({type: 'positive', message: 'Recharge LNURL copied to clipboard'})
        })
      },
      async writeNfc() {
        if (!this.selectedCard || !this.selectedCard.lnurl) return
        if (!('NDEFReader' in window)) {
          this.nfcError = true
          this.nfcMessage = 'Web NFC is not supported on this browser.'
          return
        }
        this.writingNfc = true
        this.nfcMessage = ''
        this.nfcError = false
        try {
          var ndef = new NDEFReader()
          await ndef.write({
            records: [{
              recordType: 'url',
              data: 'lightning:' + this.selectedCard.lnurl
            }]
          })
          this.written = true
          console.log('[NFC Gift Cards] written set to:', this.written)
          this.nfcError = false
          this.nfcMessage = 'Successfully wrote to NFC tag!'
          this.$q.notify({type: 'positive', message: 'NFC tag written successfully'})
        } catch (error) {
          this.nfcError = true
          this.nfcMessage = 'NFC write failed: ' + (error.message || error)
          console.error('NFC write error:', error)
        } finally {
          this.writingNfc = false
        }
      }
    },
    mounted() {
      this.nfcSupported = 'NDEFReader' in window
      var self = this
      setTimeout(function() {
        try {
          if (self.g && self.g.user && self.g.user.wallets && self.g.user.wallets.length > 0) {
            self.ready = true
            self.fetchGiftCards()
          }
        } catch (e) {}
      }, 500)
    }
  })
  console.log('[NFC Gift Cards] Vue app created successfully')
} catch (e) {
  console.error('[NFC Gift Cards] FAILED to create Vue app:', e)
}
