import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(3, '账号至少 3 位'),
  password: z.string().min(6, '密码至少 6 位'),
});

export const projectSchema = z.object({
  name: z.string().min(2, '项目名称至少 2 个字符'),
  location: z.string().max(128, '地点不能超过 128 字'),
  purpose: z.string().max(255, '用途不能超过 255 字'),
});

export const deviceSchema = z.object({
  name: z.string().min(2, '设备名称至少 2 个字符'),
  device_type_id: z.number().int().positive('请选择设备类型'),
  x: z.number().int().min(0, 'X 坐标不能小于 0').max(100, 'X 坐标不能大于 100'),
  y: z.number().int().min(0, 'Y 坐标不能小于 0').max(100, 'Y 坐标不能大于 100'),
});
