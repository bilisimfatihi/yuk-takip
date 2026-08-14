import { NextResponse } from 'next/server'
import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'

const MONGO_URL = process.env.MONGO_URL
const DB_NAME = process.env.DB_NAME || 'yuktakip'

let cachedClient = null
async function getDb() {
  if (!cachedClient) {
    cachedClient = new MongoClient(MONGO_URL)
    await cachedClient.connect()
  }
  return cachedClient.db(DB_NAME)
}

const json = (data, status = 200) => NextResponse.json(data, { status })
const err = (message, status = 400) => NextResponse.json({ error: message }, { status })

// Remove Mongo _id
const clean = (doc) => {
  if (!doc) return doc
  if (Array.isArray(doc)) return doc.map(clean)
  const { _id, ...rest } = doc
  return rest
}

// --------- STATUS CONSTANTS ---------
// created -> planning (ic_nakliye) -> planned -> in_transit -> delivered
// or created -> shipped (for non ic_nakliye)
const STATUS_LABELS = {
  created: 'Oluşturuldu',
  planning: 'Planlama Bekliyor',
  planned: 'Planlandı',
  in_transit: 'Yolda',
  delivered: 'Depoya Ulaştı',
  shipped: 'Gönderildi',
  cancelled: 'İptal',
}

// --------- ROLES ---------
const ROLES = {
  YUK_SORUMLUSU: 'yuk_sorumlusu',
  ARAC_PLANLAMA: 'arac_planlama',
  DEPOCU: 'depocu',
}

const DEMO_USERS = [
  { username: 'yukler',   password: '1234', name: 'Yük Sorumlusu Demo',   roles: [ROLES.YUK_SORUMLUSU] },
  { username: 'planlama', password: '1234', name: 'Araç Planlama Demo',   roles: [ROLES.ARAC_PLANLAMA] },
  { username: 'depo',     password: '1234', name: 'Depocu Demo',          roles: [ROLES.DEPOCU] },
]

async function ensureDemoUsers(db) {
  const col = db.collection('users')
  for (const u of DEMO_USERS) {
    const existing = await col.findOne({ username: u.username })
    if (!existing) {
      await col.insertOne({
        id: uuidv4(),
        username: u.username,
        password: u.password, // plain for MVP demo only
        name: u.name,
        roles: u.roles,
        active: true,
        createdAt: new Date().toISOString(),
      })
    }
  }
}

async function getAuthUser(request, db) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.replace(/^Bearer\s+/i, '').trim()
  if (!token) return null
  const session = await db.collection('sessions').findOne({ token })
  if (!session) return null
  const user = await db.collection('users').findOne({ id: session.userId })
  if (!user || user.active === false) return null
  return user
}

function hasAnyRole(user, roles) {
  if (!user || !Array.isArray(user.roles)) return false
  return roles.some(r => user.roles.includes(r))
}

const ALL_ROLES = [ROLES.YUK_SORUMLUSU, ROLES.ARAC_PLANLAMA, ROLES.DEPOCU]

// Determine which roles are allowed for a given (method, path).
// Returns { public: true } | { public: false, roles: [...] } | { deny: true }
function requiredRoles(method, path) {
  // Public
  if (path === 'auth/login' && method === 'POST') return { public: true }
  if (path === 'auth/init' && (method === 'POST' || method === 'GET')) return { public: true }
  if (path === 'auth/me' && method === 'GET') return { public: false, roles: ALL_ROLES }
  if (path === 'auth/logout' && method === 'POST') return { public: false, roles: ALL_ROLES }

  // Dashboard - all authenticated
  if (path === 'dashboard' && method === 'GET') return { public: false, roles: ALL_ROLES }

  // Loads
  if (path === 'loads' && method === 'GET') return { public: false, roles: ALL_ROLES }
  if (path === 'loads' && method === 'POST') return { public: false, roles: [ROLES.YUK_SORUMLUSU] }
  if (/^loads\/[^/]+$/.test(path)) {
    if (method === 'GET') return { public: false, roles: ALL_ROLES }
    if (method === 'PUT' || method === 'DELETE') return { public: false, roles: [ROLES.YUK_SORUMLUSU] }
  }
  if (/^loads\/[^/]+\/plan$/.test(path) && method === 'POST') return { public: false, roles: [ROLES.ARAC_PLANLAMA] }
  // /status - allowed for all roles but each role may only set specific statuses (enforced inside handler)
  if (/^loads\/[^/]+\/status$/.test(path) && method === 'POST') return { public: false, roles: ALL_ROLES }

  // Companies - read for all authenticated (needed to display names), write yuk_sorumlusu only
  if (path === 'companies' && method === 'GET') return { public: false, roles: ALL_ROLES }
  if (path === 'companies' && method === 'POST') return { public: false, roles: [ROLES.YUK_SORUMLUSU] }
  if (/^companies\/[^/]+$/.test(path) && (method === 'PUT' || method === 'DELETE'))
    return { public: false, roles: [ROLES.YUK_SORUMLUSU] }

  // Addresses - read for all, write yuk_sorumlusu only
  if (path === 'addresses' && method === 'GET') return { public: false, roles: ALL_ROLES }
  if (path === 'addresses' && method === 'POST') return { public: false, roles: [ROLES.YUK_SORUMLUSU] }
  if (/^addresses\/[^/]+$/.test(path) && (method === 'PUT' || method === 'DELETE'))
    return { public: false, roles: [ROLES.YUK_SORUMLUSU] }

  // Drivers - read for yuk_sorumlusu + arac_planlama, write arac_planlama only
  if (path === 'drivers' && method === 'GET') return { public: false, roles: [ROLES.YUK_SORUMLUSU, ROLES.ARAC_PLANLAMA] }
  if (path === 'drivers' && method === 'POST') return { public: false, roles: [ROLES.ARAC_PLANLAMA] }
  if (/^drivers\/[^/]+$/.test(path) && (method === 'PUT' || method === 'DELETE'))
    return { public: false, roles: [ROLES.ARAC_PLANLAMA] }

  // Vehicles - read for all, write arac_planlama only
  if (path === 'vehicles' && method === 'GET') return { public: false, roles: ALL_ROLES }
  if (path === 'vehicles' && method === 'POST') return { public: false, roles: [ROLES.ARAC_PLANLAMA] }
  if (/^vehicles\/[^/]+$/.test(path) && (method === 'PUT' || method === 'DELETE'))
    return { public: false, roles: [ROLES.ARAC_PLANLAMA] }

  // Seed - only yuk_sorumlusu (destructive), UI has been changed to not offer it once data exists
  if (path === 'seed' && method === 'POST') return { public: false, roles: [ROLES.YUK_SORUMLUSU] }

  return { deny: true }
}

async function handler(request, { params }) {
  const resolvedParams = await params
  const path = (resolvedParams?.path || []).join('/')
  const method = request.method
  const db = await getDb()

  try {
    // --- AUTHENTICATION / AUTHORIZATION GATE ---
    const perm = requiredRoles(method, path)
    if (perm.deny) return err('Endpoint bulunamadı: ' + path, 404)

    let currentUser = null
    if (!perm.public) {
      currentUser = await getAuthUser(request, db)
      if (!currentUser) return err('Yetkisiz - lütfen giriş yapın', 401)
      if (!hasAnyRole(currentUser, perm.roles)) return err('Bu işlem için yetkiniz yok', 403)
    }

    // -------- AUTH ROUTES --------
    if (path === 'auth/init' && (method === 'POST' || method === 'GET')) {
      await ensureDemoUsers(db)
      return json({
        ok: true,
        demoUsers: DEMO_USERS.map(u => ({ username: u.username, password: u.password, name: u.name, roles: u.roles })),
      })
    }

    if (path === 'auth/login' && method === 'POST') {
      await ensureDemoUsers(db)
      const body = await request.json()
      const { username, password } = body || {}
      if (!username || !password) return err('Kullanıcı adı ve şifre zorunlu', 400)
      const user = await db.collection('users').findOne({ username })
      if (!user || user.password !== password || user.active === false) {
        return err('Kullanıcı adı veya şifre hatalı', 401)
      }
      const token = uuidv4() + '.' + uuidv4()
      await db.collection('sessions').insertOne({
        token,
        userId: user.id,
        createdAt: new Date().toISOString(),
      })
      const { _id, password: _pw, ...safeUser } = user
      return json({ token, user: safeUser })
    }

    if (path === 'auth/logout' && method === 'POST') {
      const auth = request.headers.get('authorization') || ''
      const token = auth.replace(/^Bearer\s+/i, '').trim()
      if (token) await db.collection('sessions').deleteOne({ token })
      return json({ ok: true })
    }

    if (path === 'auth/me' && method === 'GET') {
      const { _id, password: _pw, ...safeUser } = currentUser
      return json(safeUser)
    }

    // -------- COMPANIES --------
    if (path === 'companies' && method === 'GET') {
      const list = await db.collection('companies').find({}).sort({ name: 1 }).toArray()
      return json(clean(list))
    }
    if (path === 'companies' && method === 'POST') {
      const body = await request.json()
      if (!body.name) return err('Firma adı zorunlu')
      const doc = {
        id: uuidv4(),
        name: body.name,
        phone: body.phone || '',
        email: body.email || '',
        active: body.active !== false,
        createdAt: new Date().toISOString(),
      }
      await db.collection('companies').insertOne(doc)
      return json(clean(doc))
    }
    if (path.startsWith('companies/') && method === 'PUT') {
      const id = path.split('/')[1]
      const body = await request.json()
      const upd = { ...body }
      delete upd.id
      await db.collection('companies').updateOne({ id }, { $set: upd })
      const d = await db.collection('companies').findOne({ id })
      return json(clean(d))
    }
    if (path.startsWith('companies/') && method === 'DELETE') {
      const id = path.split('/')[1]
      await db.collection('companies').deleteOne({ id })
      await db.collection('company_addresses').deleteMany({ companyId: id })
      return json({ ok: true })
    }

    // -------- COMPANY ADDRESSES --------
    if (path === 'addresses' && method === 'GET') {
      const url = new URL(request.url)
      const companyId = url.searchParams.get('companyId')
      const q = companyId ? { companyId } : {}
      const list = await db.collection('company_addresses').find(q).sort({ name: 1 }).toArray()
      return json(clean(list))
    }
    if (path === 'addresses' && method === 'POST') {
      const body = await request.json()
      if (!body.companyId || !body.name) return err('companyId ve adı zorunlu')
      const doc = {
        id: uuidv4(),
        companyId: body.companyId,
        name: body.name,
        address: body.address || '',
        city: body.city || '',
        district: body.district || '',
        phone: body.phone || '',
        contact: body.contact || '',
        coordinate: body.coordinate || '',
        createdAt: new Date().toISOString(),
      }
      await db.collection('company_addresses').insertOne(doc)
      return json(clean(doc))
    }
    if (path.startsWith('addresses/') && method === 'PUT') {
      const id = path.split('/')[1]
      const body = await request.json()
      const upd = { ...body }
      delete upd.id
      await db.collection('company_addresses').updateOne({ id }, { $set: upd })
      const d = await db.collection('company_addresses').findOne({ id })
      return json(clean(d))
    }
    if (path.startsWith('addresses/') && method === 'DELETE') {
      const id = path.split('/')[1]
      await db.collection('company_addresses').deleteOne({ id })
      return json({ ok: true })
    }

    // -------- DRIVERS --------
    if (path === 'drivers' && method === 'GET') {
      const list = await db.collection('drivers').find({}).sort({ name: 1 }).toArray()
      return json(clean(list))
    }
    if (path === 'drivers' && method === 'POST') {
      const body = await request.json()
      if (!body.name) return err('Ad soyad zorunlu')
      const doc = {
        id: uuidv4(),
        name: body.name,
        phone: body.phone || '',
        active: body.active !== false,
        createdAt: new Date().toISOString(),
      }
      await db.collection('drivers').insertOne(doc)
      return json(clean(doc))
    }
    if (path.startsWith('drivers/') && method === 'PUT') {
      const id = path.split('/')[1]
      const body = await request.json()
      const upd = { ...body }
      delete upd.id
      await db.collection('drivers').updateOne({ id }, { $set: upd })
      const d = await db.collection('drivers').findOne({ id })
      return json(clean(d))
    }
    if (path.startsWith('drivers/') && method === 'DELETE') {
      const id = path.split('/')[1]
      await db.collection('drivers').deleteOne({ id })
      return json({ ok: true })
    }

    // -------- VEHICLES --------
    if (path === 'vehicles' && method === 'GET') {
      const list = await db.collection('vehicles').find({}).sort({ plate: 1 }).toArray()
      return json(clean(list))
    }
    if (path === 'vehicles' && method === 'POST') {
      const body = await request.json()
      if (!body.plate) return err('Plaka zorunlu')
      const doc = {
        id: uuidv4(),
        type: body.type || '',
        plate: body.plate,
        active: body.active !== false,
        createdAt: new Date().toISOString(),
      }
      await db.collection('vehicles').insertOne(doc)
      return json(clean(doc))
    }
    if (path.startsWith('vehicles/') && method === 'PUT') {
      const id = path.split('/')[1]
      const body = await request.json()
      const upd = { ...body }
      delete upd.id
      await db.collection('vehicles').updateOne({ id }, { $set: upd })
      const d = await db.collection('vehicles').findOne({ id })
      return json(clean(d))
    }
    if (path.startsWith('vehicles/') && method === 'DELETE') {
      const id = path.split('/')[1]
      await db.collection('vehicles').deleteOne({ id })
      return json({ ok: true })
    }

    // -------- LOADS --------
    if (path === 'loads' && method === 'GET') {
      const url = new URL(request.url)
      const page = Math.max(1, parseInt(url.searchParams.get('page') || '1', 10))
      const pageSize = Math.min(200, Math.max(1, parseInt(url.searchParams.get('pageSize') || '50', 10)))
      const status = url.searchParams.get('status')
      const companyId = url.searchParams.get('companyId')
      const shipmentType = url.searchParams.get('shipmentType')
      const loadDate = url.searchParams.get('date')
      const q = (url.searchParams.get('q') || '').trim()

      const filter = {}
      if (status && status !== 'all') filter.status = status
      if (companyId && companyId !== 'all') filter.companyId = companyId
      if (shipmentType && shipmentType !== 'all') filter.shipmentType = shipmentType
      if (loadDate) filter.loadDate = loadDate

      if (q) {
        const rx = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i')
        // Also lookup companies whose name matches q, filter by those companyIds too
        const matchedCompanies = await db.collection('companies').find({ name: rx }, { projection: { id: 1 } }).toArray()
        const companyIds = matchedCompanies.map(c => c.id)
        const orClauses = [{ destCity: rx }, { destCountry: rx }]
        if (companyIds.length) orClauses.push({ companyId: { $in: companyIds } })
        filter.$or = orClauses
      }

      const total = await db.collection('loads').countDocuments(filter)
      const items = await db.collection('loads')
        .find(filter)
        .sort({ createdAt: -1 })
        .skip((page - 1) * pageSize)
        .limit(pageSize)
        .toArray()
      return json({ items: clean(items), total, page, pageSize })
    }
    if (path === 'loads' && method === 'POST') {
      const body = await request.json()
      if (!body.companyId || !body.addressId) return err('Firma ve adres zorunlu')
      const initialStatus = body.shipmentType === 'ic_nakliye' ? 'planning' : 'created'
      const now = new Date().toISOString()
      const doc = {
        id: uuidv4(),
        loadDate: body.loadDate || now.substring(0, 10),
        companyId: body.companyId,
        addressId: body.addressId,
        phone: body.phone || '',
        packages: body.packages || '',
        kg: body.kg || '',
        m3: body.m3 || '',
        dimensions: body.dimensions || '',
        destCity: body.destCity || '',
        destCountry: body.destCountry || '',
        shipmentType: body.shipmentType || 'ic_nakliye',
        note: body.note || '',
        driverId: null,
        vehicleId: null,
        plannedDateTime: null,
        status: initialStatus,
        statusHistory: [
          { status: initialStatus, at: now, user: currentUser.name || currentUser.username, note: 'Yük oluşturuldu' },
        ],
        createdAt: now,
        createdBy: currentUser.name || currentUser.username,
      }
      await db.collection('loads').insertOne(doc)
      return json(clean(doc))
    }
    if (path.startsWith('loads/') && path.split('/').length === 2 && method === 'GET') {
      const id = path.split('/')[1]
      const d = await db.collection('loads').findOne({ id })
      if (!d) return err('Yük bulunamadı', 404)
      return json(clean(d))
    }
    if (path.startsWith('loads/') && path.split('/').length === 2 && method === 'PUT') {
      const id = path.split('/')[1]
      const body = await request.json()
      const upd = { ...body }
      delete upd.id
      delete upd.statusHistory
      delete upd.createdAt
      await db.collection('loads').updateOne({ id }, { $set: upd })
      const d = await db.collection('loads').findOne({ id })
      return json(clean(d))
    }
    if (path.startsWith('loads/') && path.split('/').length === 2 && method === 'DELETE') {
      const id = path.split('/')[1]
      await db.collection('loads').deleteOne({ id })
      return json({ ok: true })
    }
    // Plan: assign driver/vehicle/datetime -> status planned
    if (path.match(/^loads\/[^/]+\/plan$/) && method === 'POST') {
      const id = path.split('/')[1]
      const body = await request.json()
      const now = new Date().toISOString()
      const load = await db.collection('loads').findOne({ id })
      if (!load) return err('Yük yok', 404)
      const newHistory = [
        ...(load.statusHistory || []),
        { status: 'planned', at: now, user: currentUser.name || currentUser.username, note: 'Araç/şoför planlandı' },
      ]
      await db.collection('loads').updateOne({ id }, { $set: {
        driverId: body.driverId || null,
        vehicleId: body.vehicleId || null,
        plannedDateTime: body.plannedDateTime || null,
        status: 'planned',
        statusHistory: newHistory,
      } })
      const d = await db.collection('loads').findOne({ id })
      return json(clean(d))
    }
    // Status change endpoint
    if (path.match(/^loads\/[^/]+\/status$/) && method === 'POST') {
      const id = path.split('/')[1]
      const body = await request.json()
      const now = new Date().toISOString()
      if (!STATUS_LABELS[body.status]) return err('Geçersiz durum')

      // Role-based status transition rules:
      // - yuk_sorumlusu: any status
      // - arac_planlama: planning, planned, in_transit, cancelled
      // - depocu: delivered only
      const allowedByRole = {
        [ROLES.YUK_SORUMLUSU]: Object.keys(STATUS_LABELS),
        [ROLES.ARAC_PLANLAMA]: ['planning', 'planned', 'in_transit', 'cancelled'],
        [ROLES.DEPOCU]: ['delivered'],
      }
      const canSet = currentUser.roles.some(r => (allowedByRole[r] || []).includes(body.status))
      if (!canSet) return err('Bu durum değişikliği için yetkiniz yok', 403)

      const load = await db.collection('loads').findOne({ id })
      if (!load) return err('Yük yok', 404)
      const newHistory = [
        ...(load.statusHistory || []),
        { status: body.status, at: now, user: currentUser.name || currentUser.username, note: body.note || '' },
      ]
      await db.collection('loads').updateOne({ id }, { $set: { status: body.status, statusHistory: newHistory } })
      const d = await db.collection('loads').findOne({ id })
      return json(clean(d))
    }

    // -------- DASHBOARD --------
    if (path === 'dashboard' && method === 'GET') {
      const col = db.collection('loads')
      const [total, pending, planning, planned, inTransit, delivered, shipped] = await Promise.all([
        col.countDocuments({}),
        col.countDocuments({ status: 'created' }),
        col.countDocuments({ status: 'planning' }),
        col.countDocuments({ status: 'planned' }),
        col.countDocuments({ status: 'in_transit' }),
        col.countDocuments({ status: 'delivered' }),
        col.countDocuments({ status: 'shipped' }),
      ])
      return json({
        total,
        pending,
        planning,
        planned: planned + inTransit,
        delivered: delivered + shipped,
      })
    }

    // -------- SEED (dev helper) --------
    if (path === 'seed' && method === 'POST') {
      // clear all
      await db.collection('companies').deleteMany({})
      await db.collection('company_addresses').deleteMany({})
      await db.collection('drivers').deleteMany({})
      await db.collection('vehicles').deleteMany({})
      await db.collection('loads').deleteMany({})

      const c1 = { id: uuidv4(), name: 'ABC Tekstil A.Ş.', phone: '02121234567', email: 'info@abctekstil.com', active: true, createdAt: new Date().toISOString() }
      const c2 = { id: uuidv4(), name: 'XYZ Makine Ltd.', phone: '02163334455', email: 'info@xyz.com', active: true, createdAt: new Date().toISOString() }
      await db.collection('companies').insertMany([c1, c2])

      const a1 = { id: uuidv4(), companyId: c1.id, name: 'Merkez Fabrika', address: 'OSB 12. Cad. No:5', city: 'İstanbul', district: 'Tuzla', phone: '02121234567', contact: 'Ahmet Yılmaz', coordinate: '', createdAt: new Date().toISOString() }
      const a2 = { id: uuidv4(), companyId: c1.id, name: 'Depo Şubesi', address: 'Sanayi Mah. 8. Sok No:11', city: 'İstanbul', district: 'Ümraniye', phone: '02165556677', contact: 'Ayşe Kaya', coordinate: '', createdAt: new Date().toISOString() }
      const a3 = { id: uuidv4(), companyId: c2.id, name: 'Ana Üretim', address: 'İvedik OSB 145. Sok', city: 'Ankara', district: 'Yenimahalle', phone: '03127778899', contact: 'Mehmet Demir', coordinate: '', createdAt: new Date().toISOString() }
      await db.collection('company_addresses').insertMany([a1, a2, a3])

      const d1 = { id: uuidv4(), name: 'Hasan Öztürk', phone: '905331234567', active: true, createdAt: new Date().toISOString() }
      const d2 = { id: uuidv4(), name: 'Ali Şahin', phone: '905339876543', active: true, createdAt: new Date().toISOString() }
      await db.collection('drivers').insertMany([d1, d2])

      const v1 = { id: uuidv4(), type: 'Kamyonet', plate: '34 ABC 123', active: true, createdAt: new Date().toISOString() }
      const v2 = { id: uuidv4(), type: 'Tır', plate: '06 XYZ 789', active: true, createdAt: new Date().toISOString() }
      await db.collection('vehicles').insertMany([v1, v2])

      return json({ ok: true, message: 'Örnek veriler yüklendi' })
    }

    return err('Endpoint bulunamadı: ' + path, 404)
  } catch (e) {
    console.error('API error:', e)
    return err(e.message || 'Sunucu hatası', 500)
  }
}

export const GET = handler
export const POST = handler
export const PUT = handler
export const DELETE = handler
export const PATCH = handler
