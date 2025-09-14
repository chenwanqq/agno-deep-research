# 参考资料管理器

## 简述
一个参考资料管理器，用于管理参考资料的添加、删除、修改、查询等操作。

## 数据结构

* id 主键
* gmt_created 创建时间
* gmt_modified 修改时间
* task_id 任务id
* task_no 在某一任务中的序号
* title 标题
* type 类型
* content 内容
* url 链接
* ext_info 扩展信息

## 功能
* insert_if_absent: 如果在同一task_id下没有相同url的参考资料，则新增一条，给这一条的task_no在这个task的范围内自增赋值；否则返回原来已存在的条目
* get_by_task_id: 根据task_id查询所有参考资料
* get_by_task_id_and_task_no: 根据task_id和task_no查询参考资料
* update: 更新参考资料
* delete: 删除参考资料

## backbone

* 第一个版本的backbone考虑用json文件存储，每一次新增参考资料时，都将所有参考资料加载到内存中，新增一条后，再将所有参考资料写回文件；
* 后续可以考虑用sqlLite等