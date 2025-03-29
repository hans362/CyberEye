{% raw %}
handleLogout() {
  axios
    .post("/api/users/logout")
    .then((response) => {
      window.location.href = "/login";
    })
    .catch(() => {
      this.$message.error("退出登录失败");
    });
},
handleMenuClick({ key }) {
  window.location.href = "/" + (key == "index" ? "" : key);
},
validatePassword(password) {
  if (!password) return false;
  if (password.length < 12) {
    return '密码长度至少12位';
  }
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`'"\\]/.test(password);
  if (!hasUpperCase || !hasLowerCase || !hasNumbers || !hasSpecialChar) {
    return '密码必须包含大小写字母、数字和特殊字符';
  } 
  return true;
},
showChangePasswordModal() {
  this.changePasswordForm = {
    old_password: '',
    new_password: '',
    confirm_password: ''
  };
  this.changePasswordVisible = true;
},
handleChangePassword() {
  if (!this.changePasswordForm.old_password || !this.changePasswordForm.new_password || !this.changePasswordForm.confirm_password) {
    this.$message.error('请填写完整信息');
    return;
  }
  if (this.changePasswordForm.new_password !== this.changePasswordForm.confirm_password) {
    this.$message.error('两次输入的新密码不一致');
    return;
  }
  const passwordValidation = this.validatePassword(this.changePasswordForm.new_password);
  if (passwordValidation !== true) {
    this.$message.error(passwordValidation);
    return;
  }
  axios.post('/api/users/me', {
    old_password: this.changePasswordForm.old_password,
    new_password: this.changePasswordForm.new_password,
  })
  .then(response => {
    if (response.data.message || response.data.detail) {
      this.$message.error(response.data.message || response.data.detail);
      return;
    }
    this.$message.success('密码修改成功');
    this.changePasswordVisible = false;
  })
  .catch(() => {
    this.$message.error('密码修改失败');
  });
},
copyToClipboard(text) {
  const input = document.createElement('input');
  input.value = text;
  document.body.appendChild(input);
  input.select();
  document.execCommand('copy');
  document.body.removeChild(input);
  this.$message.success('已复制到剪贴板');
},
diffTime(t1, t2) {
  const duration = moment.duration(moment(t2).diff(moment(t1)));
  const seconds = Math.floor(duration.asSeconds());
  const s = seconds % 60;
  const m = Math.floor(seconds / 60) % 60;
  const h = Math.floor(seconds / 3600);
  const lpad = (num) => (num < 10 ? '0' + num : num);
  return `${lpad(h)}:${lpad(m)}:${lpad(s)}`;
},
{% endraw %}