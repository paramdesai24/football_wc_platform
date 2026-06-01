import { useEffect } from 'react'
import AuctionLobbyPage from './AuctionLobbyPage'
import useAuthStore from '@/store/authStore'
import { useIdentityStore } from '@/store/identityStore'

export default function AuctionPageWrapper() {
	const { user: authUser } = useAuthStore()
	const { setUserId: setStoredUserId, setUsername: setStoredUsername } = useIdentityStore()

	useEffect(() => {
		if (authUser) {
			// Prefill identity store so auction UI shows your account
			setStoredUserId(authUser.id)
			if (authUser.username) setStoredUsername(authUser.username)
			else if (authUser.email) {
				const derived = authUser.email.split('@')[0] ?? '';
				setStoredUsername(derived);
			}
		}
	}, [authUser, setStoredUserId, setStoredUsername])

	return <AuctionLobbyPage />
}