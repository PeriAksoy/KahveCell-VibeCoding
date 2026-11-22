import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <>
      <h1>Sayfa bulunamadı</h1>
      <p>
        <Link to="/">Ana sayfaya dön</Link>
      </p>
    </>
  )
}
