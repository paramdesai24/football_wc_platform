import { useEffect } from 'react'

interface AuctionKeyboardOptions {
  onBid:          (amount: number) => void
  onConfirmSale:  () => void
  currentBid:     number
  myBudget:       number
  isCurrentHighBidder: boolean
  auctionActive:  boolean
}

export function useAuctionKeyboard({
  onBid, onConfirmSale,
  currentBid, myBudget,
  isCurrentHighBidder, auctionActive,
}: AuctionKeyboardOptions) {

  useEffect(() => {
    if (!auctionActive) return

    function handleKey(e: KeyboardEvent) {
      // Don't fire if user is typing in an input
      const tag = (e.target as HTMLElement).tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return

      switch (e.key) {
        case 'b':
        case 'B':
          // Focus the bid input
          e.preventDefault()
          document.getElementById('bid-amount-input')?.focus()
          break

        case 'Enter':
          // Submit current bid amount from input
          e.preventDefault()
          const input = document.getElementById('bid-amount-input') as HTMLInputElement
          if (input) {
            const amount = parseInt(input.value, 10)
            if (!isNaN(amount) && amount > currentBid && amount <= myBudget && !isCurrentHighBidder) {
              onBid(amount)
            }
          }
          break

        case ' ':
          // Quick-bid: current bid + minimum increment (50 coins)
          e.preventDefault()
          if (!isCurrentHighBidder) {
            const quickBid = currentBid > 0 ? currentBid + 50 : currentBid
            if (quickBid <= myBudget) onBid(quickBid)
          }
          break

        case 'Escape':
          // Clear bid input
          e.preventDefault()
          const inp = document.getElementById('bid-amount-input') as HTMLInputElement
          if (inp) {
            inp.value = ''
            inp.blur()
          }
          break

        case 'c':
        case 'C':
          // Confirm sale (host only)
          e.preventDefault()
          onConfirmSale()
          break
      }
    }

    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [auctionActive, currentBid, myBudget, isCurrentHighBidder, onBid, onConfirmSale])
}
