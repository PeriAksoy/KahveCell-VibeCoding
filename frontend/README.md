# KahveCell – Frontend

React 19 + Vite arayüzü. Proje genel bilgisi, kurulum ve demo akışı için [ana README](../README.md) dosyasına bakın.

```bash
npm install     # bağımlılıkları kur
npm run dev     # geliştirme sunucusu: http://localhost:5173
npm run lint    # kod denetimi
npm run build   # üretim derlemesi
```

Backend adresi `VITE_API_URL` ile ayarlanır (varsayılan `http://localhost:8000`, bkz. `.env.example`).
Backend yalnızca `http://localhost:5173` adresinden gelen isteklere izin verdiği için port sabittir.
