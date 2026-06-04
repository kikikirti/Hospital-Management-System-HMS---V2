import { createRouter, createWebHistory } from "vue-router";
import { isLoggedIn, getRole } from "../services/auth";

import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import Register from "../views/Register.vue";

import AdminLayout from "../views/Admin.vue";
import AdminDashboard from "../views/admin/AdminDashboard.vue";
import AdminDoctors from "../views/admin/AdminDoctors.vue";
import AdminPatients from "../views/admin/AdminPatients.vue";
import AdminAppointments from "../views/admin/AdminAppointments.vue";
import AdminDepartments from "../views/admin/AdminDepartments.vue";

import DoctorLayout from "../views/Doctor.vue";
import DoctorDashboard from "../views/doctor/DoctorDashboard.vue";
import DoctorAppointments from "../views/doctor/DoctorAppointments.vue";
import DoctorAvailability from "../views/doctor/DoctorAvailability.vue";
import DoctorPatients from "../views/doctor/DoctorPatients.vue";
import DoctorPatientHistory from "../views/doctor/DoctorPatientHistory.vue";
import DoctorProfile from "../views/doctor/DoctorProfile.vue";

import PatientLayout from "../views/Patient.vue";
import PatientDashboard from "../views/patient/PatientDashboard.vue";
import PatientDoctors from "../views/patient/PatientDoctors.vue";
import PatientBookAppointment from "../views/patient/PatientBookAppointment.vue";
import PatientAppointments from "../views/patient/PatientAppointments.vue";
import PatientReschedule from "../views/patient/PatientReschedule.vue";
import PatientHistory from "../views/patient/PatientHistory.vue";
import PatientProfile from "../views/patient/PatientProfile.vue";

const routes = [
  { path: "/", component: Home },
  { path: "/login", component: Login },
  { path: "/register", component: Register },

  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true, role: "admin" },
    children: [
      { path: "", redirect: "/admin/dashboard" },
      { path: "dashboard", component: AdminDashboard },
      { path: "doctors", component: AdminDoctors },
      { path: "patients", component: AdminPatients },
      { path: "appointments", component: AdminAppointments },
      { path: "departments", component: AdminDepartments },
    ],
  },

  {
    path: "/doctor",
    component: DoctorLayout,
    meta: { requiresAuth: true, role: "doctor" },
    children: [
      { path: "", redirect: "/doctor/dashboard" },
      { path: "dashboard", component: DoctorDashboard },
      { path: "appointments", component: DoctorAppointments },
      { path: "availability", component: DoctorAvailability },
      { path: "patients", component: DoctorPatients },
      { path: "patients/:id", component: DoctorPatientHistory, props: true },
      { path: "profile", component: DoctorProfile },
    ],
  },

    {
    path: "/patient",
    component: PatientLayout,
    meta: { requiresAuth: true, role: "patient" },
    children: [
      { path: "", redirect: "/patient/dashboard" },
      { path: "dashboard", component: PatientDashboard },
      { path: "doctors", component: PatientDoctors },
      { path: "doctors/:doctorId/book", component: PatientBookAppointment, props: true },
      { path: "appointments", component: PatientAppointments },
      { path: "appointments/:apptId/reschedule", component: PatientReschedule, props: true },
      { path: "history", component: PatientHistory },
      { path: "profile", component: PatientProfile },
    ],
  },

  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

function routeForRole(role) {
  if (role === "admin") return "/admin/dashboard";
  if (role === "doctor") return "/doctor/dashboard";
  if (role === "patient") return "/patient/dashboard";
  return "/login";
}

router.beforeEach((to, from, next) => {
  const loggedIn = isLoggedIn();
  const role = getRole();

  const publicPages = ["/", "/login", "/register"];
  const isPublicPage = publicPages.includes(to.path);

  if (!loggedIn && !isPublicPage) {
    return next("/login");
  }

  if (loggedIn && isPublicPage) {
    return next(routeForRole(role));
  }

  const requiredRole = to.matched.find((record) => record.meta?.role)?.meta?.role;
  if (requiredRole && role !== requiredRole) {
    return next(routeForRole(role));
  }

  next();
});

export default router;
