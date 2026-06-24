# Java集合

重要性等级：S=至尊（必考，频率>80%） A=高级（高频，频率50%-80%） B=基础（中频，频率30%-50%） C=普通（低频，<30%）

# 概念

## 说说Java中的集合？ [重要性:S]

**List** 是有序的 Collection，使用此接口能够精确的控制每个元素的插入位置，用户能根据索引访问 List 中元素。常用的实现 List 的类有 LinkedList，ArrayList，Vector，Stack。
- **ArrayList** 是容量可变的非线程安全列表，其底层使用数组实现。当集合扩容时，会创建更大的数组，并把原数组复制到新数组。ArrayList 支持对元素的快速随机访问，在尾部追加/删除元素效率很高，但在中间位置插入/删除需要搬移元素，代价较高。
- **LinkedList** 本质是一个双向链表，支持高效的头尾插入/删除和作为双端队列使用。需要注意的是："LinkedList 插入/删除比 ArrayList 更快"是一个常见误区：其 O(1) 的前提是已经持有目标节点的引用；如果要在任意位置插入/删除，仍需先 O(n) 遍历链表找到位置，加上每个节点都需要独立分配、对 CPU 缓存不友好，实测大多数场景下 LinkedList 反而比 ArrayList 慢，这也是现在主流建议优先使用 ArrayList 的原因。

**Set** 不允许存在重复的元素，与 List 不同，set 中的元素是无序的。常用的实现有 HashSet，LinkedHashSet 和 TreeSet。
- **HashSet** 通过 HashMap 实现，HashMap 的 Key 即 HashSet 存储的元素，所有 Key 都是用相同的 Value，一个名为 PRESENT 的 Object 类型常量。使用 Key 保证元素唯一性，但不保证有序性。由于其底层的 HashMap 本身就是非线程安全的，因此 HashSet 也是非线程安全的。
- **LinkedHashSet** 继承自 HashSet，通过 LinkedHashMap 实现，使用双向链表维护元素插入顺序。
- **TreeSet** 通过 TreeMap 实现的，添加元素到集合时按照比较规则将其插入合适的位置，保证插入后的集合仍然有序。

**Map** 是一个键值对集合，存储键、值和之间的映射。Key 无序，唯一；value 不要求有序，允许重复。Map 没有继承于 Collection 接口，从 Map 集合中检索元素时，只要给出键对象，就会返回对应的值对象。主要实现有 TreeMap、HashMap、Hashtable、LinkedHashMap、ConcurrentHashMap。
- **HashMap**：JDK1.8 之前 HashMap 由数组+链表组成的，数组是 HashMap 的主体，链表则是主要为了解决哈希冲突而存在的（"拉链法"解决冲突），JDK1.8 以后在解决哈希冲突时有了较大的变化：当某个桶的链表长度 ≥ 8 且哈希表数组长度 ≥ 64 时，才会将该链表转化为红黑树，以减少搜索时间；如果数组长度 < 64，则只会触发扩容而不做树化。
- **LinkedHashMap**：LinkedHashMap 继承自 HashMap，所以它的底层仍然是基于拉链式散列结构即由数组和链表或红黑树组成。另外，LinkedHashMap 在上面结构的基础上，增加了一条双向链表，使得上面的结构可以保持键值对的插入顺序。同时通过对链表进行相应的操作，实现了访问顺序相关逻辑。
- **Hashtable**：数组+链表组成的，数组是 Hashtable 的主体，链表则是主要为了解决哈希冲突而存在的。
- **TreeMap**：红黑树（自平衡的排序二叉树）。
- **ConcurrentHashMap**：Node 数组+链表+红黑树实现，线程安全的（jdk1.8 以前 Segment 锁，1.8 以后 volatile + CAS 或者 synchronized）。

![Java集合框架总览](zmedia/Java集合面试题_images/02_java_collections_overview.webp)

---

## Java中的线程安全的集合是什么？ [重要性:S]


`java.util.concurrent` 包提供的都是线程安全的集合：
- **并发 Map**：
  - **ConcurrentHashMap**：它与 Hashtable 的主要区别是二者加锁粒度的不同，在 JDK 1.7，ConcurrentHashMap 加的是分段锁，也就是 Segment 锁，每个 Segment 含有整个 table 的一部分，这样不同分段之间的并发操作就互不影响。在 JDK 1.8，它取消了 Segment，直接在 table 元素（桶的头节点）上加锁，使加锁粒度进一步缩小到单个桶级别。对于 put 操作，如果 Key 对应的数组槽位为 null，则通过 CAS 操作（Compare and Swap）将新节点写入该槽位；如果槽位不为 null（即已存在链表头或红黑树根节点），则对该头节点使用 synchronized 加锁，然后遍历桶中的数据执行替换或新增。如果该 put 操作使得当前桶的链表长度超过阈值，则将其转换为红黑树，从而提高查找效率。
  - **ConcurrentSkipListMap**：实现了一个基于 SkipList（跳表）算法的可排序的并发集合，SkipList 是一种可以在对数预期时间内完成搜索、插入、删除等操作的数据结构，通过维护多个指向其他元素的"跳跃"链接来实现高效查找。
- **并发 Set**：
  - **ConcurrentSkipListSet**：是线程安全的有序的集合。底层是使用 ConcurrentSkipListMap 实现。
  - **CopyOnWriteArraySet**：是线程安全的 Set 实现，它是线程安全的无序的集合，可以将它理解成线程安全的 HashSet。有意思的是，CopyOnWriteArraySet 和 HashSet 虽然都继承于共同的父类 AbstractSet；但是，HashSet 是通过"散列表"实现的，而 CopyOnWriteArraySet 则是通过"动态数组(CopyOnWriteArrayList)"实现的，并不是散列表。
- **并发 List**：
  - **CopyOnWriteArrayList**：它是 ArrayList 的线程安全的变体，其中所有写操作（add，set 等）都通过对底层数组进行全新复制来实现，允许存储 null 元素。即当对象进行写操作时，使用了 Lock 锁做同步处理，内部拷贝了原数组，并在新数组上进行添加操作，最后将新数组替换掉旧数组；若进行的读操作，则直接返回结果，操作过程中不需要进行同步。
- **并发 Queue**：
  - **ConcurrentLinkedQueue**：是一个适用于高并发场景下的队列，它通过无锁的方式(CAS)，实现了高并发状态下的高性能。通常，ConcurrentLinkedQueue 的性能要好于 BlockingQueue。
  - **BlockingQueue**：与 ConcurrentLinkedQueue 的使用场景不同，BlockingQueue 的主要功能并不是在于提升高并发时的队列性能，而在于简化多线程间的数据共享。BlockingQueue 提供一种读写阻塞等待的机制，即如果消费者速度较快，则 BlockingQueue 则可能被清空，此时消费线程再试图从 BlockingQueue 读取数据时就会被阻塞。反之，如果生产线程较快，则 BlockingQueue 可能会被装满，此时，生产线程再试图向 BlockingQueue 队列装入数据时，便会被阻塞等待。
- **并发 Deque**：
  - **LinkedBlockingDeque**：是一个线程安全的双端队列实现。它的内部使用链表结构，每一个节点都维护了一个前驱节点和一个后驱节点。LinkedBlockingDeque 没有进行读写锁的分离，因此同一时间只能有一个线程对其进行操作。
  - **ConcurrentLinkedDeque**：ConcurrentLinkedDeque 是一种基于链接节点的无限并发链表。可以安全地并发执行插入、删除和访问操作。当许多线程同时访问一个公共集合时，ConcurrentLinkedDeque 是一个合适的选择。

---


## list可以一边遍历一边修改元素吗？ [重要性:A]

在 Java 中，List 在遍历过程中是否可以修改元素取决于遍历方式和具体的 List 实现类：

**1. 使用普通 for 循环遍历**：可以在遍历过程中修改元素，只要修改的索引不超出 List 的范围即可。

```java
import java.util.ArrayList;
import java.util.List;

public class ListTraversalAndModification {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);

        // 使用普通for循环遍历并修改元素
        for (int i = 0; i < list.size(); i++) {
            list.set(i, list.get(i) * 2);
        }

        System.out.println(list);
    }
}
**2. 使用 foreach 循环遍历**：一般不建议在 foreach 循环中直接修改集合结构（add/remove），因为 foreach 底层基于迭代器实现，集合结构被修改后，迭代器下一次调用 next() 时会检测到 modCount != expectedModCount，从而抛出 `ConcurrentModificationException` 异常。注意："替换元素值"（即 `list.set(i, newValue)`）并不会改变 modCount，所以 `list.set()` 本身不会抛 CME；但 `list.add()` / `list.remove()` 会。
```java
import java.util.ArrayList;
import java.util.List;
public class ListTraversalAndModification {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);
        list.add(4);
        // 在foreach中调用list.add/remove会抛出ConcurrentModificationException
        for (Integer num : list) {
            if (num == 2) {
                list.remove(num); // 修改了结构，下一次迭代会抛CME
            }
        }
        System.out.println(list);
    }
}

**3. 使用迭代器遍历时**：如果需要在遍历过程中删除元素，应使用 `Iterator.remove()`；如果需要替换元素，使用 `ListIterator.set()` 是最通用、最推荐的做法。

```java
import java.util.ArrayList;
import java.util.ListIterator;

public class ListTraversalAndModification {
    public static void main(String[] args) {
        ArrayList<Integer> list = new ArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);

        // 使用 ListIterator 遍历并修改元素
        ListIterator<Integer> iterator = list.listIterator();
        while (iterator.hasNext()) {
            Integer num = iterator.next();
            if (num.equals(2)) {
                // 使用 ListIterator 的 set 方法修改（替换）元素
                iterator.set(4);
            }
        }

        System.out.println(list); // 输出: [1, 4, 3]
    }
}
对于线程安全的 List，如 CopyOnWriteArrayList，由于其采用了写时复制的机制，在遍历的同时可以进行修改操作，不会抛出 `ConcurrentModificationException` 异常，但可能会读取到旧的数据，因为修改操作是在新的副本上进行的。
---
## ArrayList线程安全吗？把ArrayList变成线程安全有哪些方法？ [重要性:S]
不是线程安全的。将 ArrayList 变成线程安全的方式有：
```java
// 1. 使用Collections类的synchronizedList方法将ArrayList包装成线程安全的List
List<String> synchronizedList = Collections.synchronizedList(arrayList);
// 2. 使用CopyOnWriteArrayList类代替ArrayList
CopyOnWriteArrayList<String> copyOnWriteArrayList = new CopyOnWriteArrayList<>(arrayList);
// 3. 使用Vector类代替ArrayList
Vector<String> vector = new Vector<>(arrayList);

---

## ArrayList 和 LinkedList 的应用场景？ [重要性:A]
- **ArrayList** 适用于需要频繁访问集合元素的场景。它基于数组实现，可以通过索引快速访问元素，因此在按索引查找、遍历和随机访问元素的操作上具有较高的性能。当需要频繁访问和遍历集合元素，并且集合大小不经常改变时，推荐使用 ArrayList。
- **LinkedList** 适用于频繁进行插入和删除操作的场景。它基于链表实现，插入和删除元素的操作只需要调整节点的指针，因此在插入和删除操作上具有较高的性能。当需要频繁进行插入和删除操作，或者集合大小经常改变时，可以考虑使用 LinkedList。

---

## 线程安全的 List，CopyonWriteArraylist是如何实现线程安全的 [重要性:A]

CopyOnWriteArrayList 底层也是通过一个数组保存数据，使用 volatile 关键字修饰数组，保证当前线程对数组对象重新赋值后，其他线程可以及时感知到。

```java
private transient volatile Object[] array;
```

**写入操作**时，加了一把互斥锁 `ReentrantLock` 以保证线程安全：

```java
public boolean add(E e) {
    //获取锁
    final ReentrantLock lock = this.lock;
    //加锁
    lock.lock();
    try {
        //获取到当前List集合保存数据的数组
        Object[] elements = getArray();
        //获取该数组的长度
        int len = elements.length;
        //将当前数组拷贝一份的同时，让其长度加1
        Object[] newElements = Arrays.copyOf(elements, len + 1);
        //将加入的元素放在新数组最后一位
        newElements[len] = e;
        //替换引用，将数组的引用指向给新数组的地址
        setArray(newElements);
        return true;
    } finally {
        //释放锁
        lock.unlock();
    }
}
```

在替换地址操作之前，读取的是老数组的数据；执行替换地址操作之后，读取的是新数组的数据，都是有效数据。

**读操作**是没有加锁的，所以读是一直都能读：

```java
public E get(int index) {
    return get(getArray(), index);
}
---
## HashMap实现原理介绍一下？ [重要性:S]
在 JDK 1.7 版本之前，HashMap 数据结构是数组和链表。HashMap 通过哈希算法将元素的键（Key）映射到数组中的槽位（Bucket）。如果多个键映射到同一个槽位，它们会以链表的形式存储在同一个槽位上，因为链表的查询时间是 O(n)，所以冲突很严重时效率就很低了。
在 JDK 1.8 版本的时候做了优化：当某个桶的链表长度 ≥ 8（TREEIFY_THRESHOLD）且哈希表数组长度 ≥ 64（MIN_TREEIFY_CAPACITY）时，会把链表转换为红黑树，把该桶的查找时间复杂度从 O(n) 降低到 O(log n)；如果数组长度 < 64，则只会触发扩容（resize()），并不会立刻树化。反向地，在 resize() 过程中，若某个桶的节点数 ≤ 6（UNTREEIFY_THRESHOLD），红黑树会被退化回链表。
![HashMap JDK 1.7 结构（数组+链表）](zmedia/Java集合面试题_images/08_hashmap_before_8.webp)
*JDK 1.7 HashMap：数组 + 链表*
![HashMap JDK 1.8 结构（数组+链表+红黑树）](zmedia/Java集合面试题_images/09_hashmap_after_8.webp)
*JDK 1.8 HashMap：数组 + 链表 + 红黑树*
---
## 了解的哈希冲突解决方法有哪些？ [重要性:A]
1. **链接法**：使用链表或其他数据结构来存储冲突的键值对，将它们链接在同一个哈希桶中。
2. **开放寻址法**：在哈希表中找到另一个可用的位置来存储冲突的键值对。常见的开放寻址方法包括线性探测、二次探测和双重散列。
3. **再哈希法（Rehashing）**：当发生冲突时，使用另一个哈希函数再次计算键的哈希值，直到找到一个空槽来存储键值对。
4. **哈希桶扩容**：当哈希冲突过多时，可以动态地扩大哈希桶的数量，重新分配键值对，以减少冲突的概率。
---
## 在 Java 的 hashmap 中 get一个元素的过程是怎样的？ [重要性:S]
`get` 方法的作用是传入我们需要获取的节点的 key，然后将这个节点的 value 返回。
```java
public V get(Object key) {
    Node<K,V> e;
    return (e = getNode(hash(key), key)) == null ? null : e.value;
}

`getNode` 方法的源码解读：

```java
final HashMap.Node<K,V> getNode(int hash, Object key) {
    HashMap.Node<K,V>[] tab; HashMap.Node<K,V> first, e; int n; K k;

    // 判断条件：table不为null、长度大于0、hash值计算出的位置有节点存在
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (first = tab[(n - 1) & hash]) != null) {

        // 先判断第一个节点的key是否匹配
        if (first.hash == hash &&
            ((k = first.key) == key || (key != null && key.equals(k))))
            return first;

        // 遍历后续节点
        if ((e = first.next) != null) {
            // 如果是树节点，用红黑树查找算法
            if (first instanceof HashMap.TreeNode)
                return ((HashMap.TreeNode<K,V>)first).getTreeNode(hash, key);
            // 否则遍历链表
            do {
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    return e;
            } while ((e = e.next) != null);
        }
    }
    return null;
}
```
---
## HashMap的put(key,val)和get(key)过程 [重要性:S]
存储对象时，将 K/V 传给 put 方法时，它调用 hashCode 计算 hash 从而得到 bucket 位置，进一步存储。HashMap 在每次 put 后会检查整个表的元素数量（size），当 size > 容量 × loadFactor（默认 16 × 0.75 = 12）时触发扩容，新容量为原来的 2 倍。
获取对象时，将 K 传给 get，它调用 hashCode 计算 hash 从而得到 bucket 位置，并进一步调用 equals() 方法确定键值对。如果发生碰撞的时候，Hashmap 通过链表将产生碰撞冲突的元素组织起来，在 Java 8 中，如果一个 bucket 中碰撞冲突的元素超过某个限制（默认是 8），则使用红黑树来替换链表，从而提高速度。
---
## hashmap 调用get方法一定安全吗？ [重要性:A]
不是，调用 get 方法有几点需要注意的地方：
1. **空指针异常（NullPointerException）**：
   - 如果 HashMap 变量本身是 null（还没 new），那么调用它的任何方法都会抛 NPE。
   - 如果 HashMap 已经正常初始化，那么用 null 作为 key 调用 `get(null)` / `put(null, v)` 都是合法的，不会抛 NPE，因为 HashMap 明确支持 null 键。
2. **线程安全**：HashMap 本身不是线程安全的。如果在多线程环境中，没有适当的同步措施，同时对 HashMap 进行读写操作可能会导致不可预测的行为。
---
## HashMap一般用什么做Key？为啥String适合做Key呢？ [重要性:A]
用 String 做 key，因为 String 对象是不可变的，一旦创建就不能被修改，这确保了 Key 的稳定性。如果 Key 是可变的，可能会导致 hashCode 和 equals 方法的不一致，进而影响 HashMap 的正确性。
---
## 为什么HashMap要用红黑树而不是平衡二叉树？ [重要性:A]
平衡二叉树追求的是一种"完全平衡"状态：任何结点的左右子树的高度差不会超过 1。这个要求太严了，导致每次进行插入/删除节点的时候，几乎都会破坏平衡规则，需要频繁通过左旋和右旋来进行调整。
红黑树不追求这种完全平衡状态，而是追求一种"弱平衡"状态：整个树最长路径不会超过最短路径的 2 倍。优势是虽然牺牲了一部分查找的性能效率，但是能够换取一部分维持树平衡状态的成本。与平衡树不同的是，红黑树在插入、删除等操作，不会像平衡树那样，频繁破坏红黑树的规则，所以不需要频繁调整。
---
## hashmap key可以为null吗？ [重要性:A]
可以为 null。
- HashMap 中使用 `hash()` 方法来计算 key 的哈希值，当 key 为空时，直接令 key 的哈希值为 0，不走 `key.hashCode()` 方法。
- HashMap 虽然支持 key 和 value 为 null，但是 null 作为 key 只能有一个，null 作为 value 可以有多个。
- 因为 HashMap 中，如果 key 值一样，那么会覆盖相同 key 值的 value 为最新，所以 key 为 null 只能有一个。
---
## 重写HashMap的equal和hashcode方法需要注意什么？ [重要性:S]
HashMap 使用 Key 对象的 `hashCode()` 和 `equals` 方法去决定 key-value 对的索引。如果这些方法没有被正确地实现，两个不同 Key 也许会产生相同的 `hashCode()` 和 `equals()` 输出，HashMap 将会认为它们是相同的，然后覆盖它们。
`equals()` 和 `hashCode()` 的实现应该遵循以下规则：
- 如果 `o1.equals(o2)`，那么 `o1.hashCode() == o2.hashCode()` 总是为 true 的。
- 如果 `o1.hashCode() == o2.hashCode()`，并不意味着 `o1.equals(o2)` 会为 true。
---
## 重写HashMap的equal方法不当会出现什么问题？ [重要性:A]
HashMap 在比较元素时，会先通过 hashCode 进行比较，相同的情况下再通过 equals 进行比较。
所以 equals 相等的两个对象，hashCode 一定相等。hashCode 相等的两个对象，equals 不一定相等（比如散列冲突的情况）。
重写了 equals 方法，不重写 hashCode 方法时，可能会出现 equals 方法返回为 true，而 hashCode 方法却返回 false，这样的后果会导致在 HashMap 等类中存储多个一模一样的对象，导致出现覆盖存储的数据的问题。
---
## 列举HashMap在多线程下可能会出现的问题？ [重要性:S]
1. **JDK 1.7 中的环形链表问题**：使用头插法插入元素，在多线程的环境下，扩容的时候有可能导致环形链表的出现，形成死循环。JDK 1.8 使用尾插法插入元素，在扩容时会保持链表元素原本的顺序，不会出现环形链表的问题。
2. **数据覆盖**：多线程同时执行 put 操作，如果计算出来的索引位置是相同的，那会造成前一个 key 被后一个 key 覆盖，从而导致元素的丢失。此问题在 JDK 1.7 和 JDK 1.8 中都存在。
---
## HashMap的扩容机制介绍一下 [重要性:S]
HashMap 默认的负载因子是 0.75，即如果 HashMap 中的元素个数超过了总容量 75%，则会触发扩容。扩容分为两个步骤：
1. 对哈希表长度的扩展（2 倍）
2. 将旧哈希表中的数据放到新的哈希表中
因为我们使用的是 2 次幂的扩展（指长度扩为原来 2 倍），所以元素的位置要么是在原位置，要么是在原位置再移动 2 次幂的位置。
因此在扩充 HashMap 时，不需要重新计算 hash，只需要看看原来的 hash 值新增的那个 bit 是 1 还是 0：
- 是 0 的话索引没变
- 是 1 的话索引变成"原索引 + oldCap"
这个设计既省去了重新计算 hash 值的时间，而且由于新增的 1bit 是 0 还是 1 可以认为是随机的，因此 resize 的过程均匀地把之前冲突的节点分散到新的 bucket 了。
![HashMap 扩容示意图](zmedia/Java集合面试题_images/11_hashmap_resize.png)
*HashMap 扩容（resize）流程*
---
## HashMap的大小为什么是2的n次方大小呢？ [重要性:S]
HashMap 底层是"数组 + 链表/红黑树"的结构，存的 key-value 时，第一步就是确定这个 key 存在数组的哪个位置（索引）。
HashMap 用的索引计算公式是：**索引 = hash & (length - 1)**
这个公式的设计初衷是用位运算替代取模运算，但它能生效的前提，就是 **length 必须是 2 的 n 次方**。
### 原因 1：保证"位运算等价于取模"，实现高效寻址
当 length 是 2 的 n 次方时，length - 1 的二进制低 n 位全是 1，高位全是 0。此时做"与运算"，相当于直接把 hash 值的低 n 位截取下来，在数学上等价于"对 length 取模"。
反例：如果 length = 15（不是 2 的 n 次方），length - 1 = 14，二进制是 00001110（最后一位是 0）。不管 hash 值的最后一位是 0 还是 1，与运算后都会变成 0——这就导致索引的最后一位永远用不到，比如索引 1、3、5、7... 这些位置永远不会存数据，既浪费了数组空间，又大大增加了哈希碰撞的概率。
### 原因 2：让哈希值的低位更均匀，减少碰撞
只有当 length - 1 的二进制是全 1 时，才能"接住"hash 值的均匀分布。比如 length=16 时，length-1=15（1111），hash 值的低 4 位每一位都能影响最终索引；如果 length=15，length-1=14（1110），最后一位直接失效，相当于少了一位来分散 hash，碰撞概率自然就高了。
### 原因 3：优化扩容时的元素重分配，不用重新算 hash
如果容量始终是 2 的 n 次方，扩容时元素的新索引就不用重新计算完整的 hash，只需要看 hash 值的某一个高位就行：
- 计算 `hash & oldCap`：如果结果为 0，新索引 = 旧索引；如果结果不为 0，新索引 = 旧索引 + oldCap。
整个过程只需要做一次"与运算"，速度非常快。而且还能把原来挤在同一个旧索引里的元素，均匀拆分到新数组的两个索引位。
![索引位运算示例](zmedia/Java集合面试题_images/12_hash_index_calc.webp)
*hash & (length - 1) 位运算示例*
![扩容 rehash 原理](zmedia/Java集合面试题_images/13_resize_rehash.webp)
*扩容时元素重新分布：无需重新计算 hash*
![扩容元素分布](zmedia/Java集合面试题_images/14_resize_redistribute.webp)
*16 扩容到 32 时元素的均匀拆分*
### 总结
HashMap 的大小设计为 2 的 n 次方，是一个环环相扣的优化设计：
1. 保证 `hash & (length - 1)` 等价于取模，用位运算实现高效寻址
2. 让 `length - 1` 的二进制全 1，接住 hash 值的均匀分布，减少碰撞
3. 为扩容优化铺路，不用重新算 hash，仅通过高位判断就能快速确定新索引
---
## 往hashmap存20个元素，会扩容几次？ [重要性:A]
当插入 20 个元素时，HashMap 的扩容过程如下：
- **初始容量**：16
  - 插入第 1 到第 12 个元素时，不需要扩容。
  - 插入第 13 个元素时，达到负载因子限制，需要扩容（16 → 32）。
- **扩容后的容量**：32
  - 插入第 14 到第 24 个元素时，不需要扩容。
因此，总共会进行一次扩容。
---
## 说说hashmap的负载因子 [重要性:S]
HashMap 负载因子 `loadFactor` 的默认值是 0.75，当 HashMap 中的元素个数超过了容量的 75% 时，就会进行扩容。
默认负载因子为 0.75，是因为它提供了空间和时间复杂度之间的良好平衡。负载因子太低会导致大量的空桶浪费空间，负载因子太高会导致大量的碰撞，降低性能。0.75 在这两个因素之间取得了良好的平衡。
---
## ConcurrentHashMap怎么实现的？ [重要性:S]
### JDK 1.7 ConcurrentHashMap
使用数组加链表的形式实现，数组分为大数组 Segment 和小数组 HashEntry。Segment 是一种可重入锁（ReentrantLock），在 ConcurrentHashMap 里扮演锁的角色。分段锁技术将数据分成一段一段的存储，然后给每一段数据配一把锁，当一个线程占用锁访问其中一个段数据的时候，其他段的数据也能被其他线程访问。
![ConcurrentHashMap JDK 1.7 结构（分段锁）](zmedia/Java集合面试题_images/15_concurrenthashmap_17.webp)
*JDK 1.7 ConcurrentHashMap：Segment + HashEntry 分段锁*
### JDK 1.8 ConcurrentHashMap
主要使用 volatile + CAS 或者 synchronized 来实现线程安全：
- 添加元素时首先会判断容器是否为空：
  - 如果根据存储的元素计算结果为空，则利用 CAS 设置该节点
  - 如果根据存储的元素计算结果不为空，则使用 synchronized，然后遍历桶中的数据，并替换或新增节点到桶中
  - 最后再判断是否需要转为红黑树
JDK 1.8 通过对头结点加锁来保证线程安全，锁的粒度相比 Segment 更小了，并发操作的性能提高了。而且使用红黑树优化了之前的固定链表，查询性能从 O(n) 优化到了 O(log n)。
![ConcurrentHashMap JDK 1.8 结构（CAS + synchronized）](zmedia/Java集合面试题_images/16_concurrenthashmap_18.webp)
*JDK 1.8 ConcurrentHashMap：CAS + volatile + synchronized*
---
## JDK 1.7 中的分段锁是怎么加锁的？ [重要性:A]
注意：分段锁是 JDK 1.7 ConcurrentHashMap 的实现，JDK 1.8 之后已经废弃了 Segment，改为对桶头节点加 synchronized。
在 JDK 1.7 的 ConcurrentHashMap 中，将整个数据结构分为多个 Segment，每个 Segment 都类似于一个小的 HashMap，每个 Segment 都有自己的锁，不同 Segment 之间的操作互不影响。
对于插入、更新、删除等操作，需要先定位到具体的 Segment，然后再在该 Segment 上加锁，而不是像 Hashtable 那样对整个表加锁。
---
## 已经用了synchronized，为什么还要用CAS呢？ [重要性:A]
ConcurrentHashMap 使用这两种手段来保证线程安全是一种权衡的考虑，根据锁竞争程度来判断：
- 在 `putVal` 中，如果计算出来的 hash 槽没有存放元素，可以直接使用 CAS 来进行设置值。因为 hash 值经过了各种扰动后，造成 hash 碰撞的几率较低，可以使用较少的自旋来完成具体的 hash 落槽操作。
- 当桶位已经存在节点（发生 hash 碰撞）时，需要遍历链表或红黑树进行查找、替换或追加节点，操作步骤较多且需要保护整条链/树的结构，CAS 自旋已经不再适合，因此改用 synchronized 锁住桶的头节点来完成这部分逻辑。
---
## ConcurrentHashMap用了悲观锁还是乐观锁? [重要性:A]
悲观锁和乐观锁都有用到。
- 如果容器为空，或计算结果为空：使用 volatile 加 **CAS（乐观锁）** 来初始化/设置节点。
- 如果计算结果不为空：使用 **synchronized（悲观锁）**，遍历桶中的数据，替换或新增节点到桶中，最后判断是否需要转为红黑树。
---
## 说一下HashMap和Hashtable、ConcurrentMap的区别 [重要性:A]
**HashMap**：线程不安全，效率高，可以存储 null 的 key 和 value。默认初始容量为 16，每次扩充变为原来 2 倍。底层数据结构为数组+链表，插入元素后如果链表长度大于阈值（默认为8），先判断数组长度是否小于64，如果小于则扩充数组，反之将链表转化为红黑树。
**Hashtable**：线程安全（synchronized），效率低，不可以有 null 的 key 和 value。默认初始容量为 11，每次扩容变为原来的 2n+1。底层数据结构为数组+链表。基本被淘汰了。
**ConcurrentHashMap**：线程安全，不支持 null key 或 null value（会抛 NPE），原因是多线程下 null 无法区分"key 不存在"还是"key 对应的 value 就是 null"。
- JDK 1.7 及以前：基于分段锁实现
- JDK 1.8 及以后：取消 Segment，基于 volatile + CAS + synchronized，锁粒度从"段"缩小到"桶"
---
# Set
## Set集合有什么特点？如何实现key无重复的？ [重要性:A]
**特点**：Set 集合中的元素是唯一的，不会出现重复的元素。
**实现原理**：
- **HashSet / LinkedHashSet**：底层是哈希表，插入元素时先用 `hashCode()` 定位桶，再用 `equals()` 比较是否已存在相同元素，存在则不再插入。
- **TreeSet**：底层是红黑树，插入元素时不调用 hashCode/equals，而是用 `Comparable.compareTo()`（自然排序）或自定义 `Comparator.compare()` 的返回值是否为 0 来判断是否重复。
